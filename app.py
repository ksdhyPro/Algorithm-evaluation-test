from flask import Flask, request,  jsonify, send_from_directory
import re
from flask_cors import CORS
import os
import json
import shutil
import time
import threading
from datetime import datetime
from werkzeug.utils import secure_filename
from config import BASE_DIR, UPLOAD_FOLDER, ZIP_MAX_SIZE, TAR_MAX_SIZE, IMAGE_MAX_SIZE
from logger import logger
from docker_utils import get_docker_stats, periodic_cleanup
from utils import (
    load_users,
    extract_zip_to_folder,
    allowed_tar_file,
    allowed_zip_file,
    allowed_image_file,
    normalize_rel_path,
    get_disk_free_bytes,
    is_disk_space_sufficient,
)
from services.contests import (
    generate_contest_id,
    contest_paths,
    get_all_contests,
    get_contest_submissions,
)
from services.submissions import append_submission_record
from task_queue import enqueue_task, queue_size
from queue_runner import run_queue_worker

app = Flask(__name__)

STATIC_ROOT = os.path.join(os.path.dirname(__file__), "web")

# 初始化：创建必要的目录
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 启用跨域资源共享 (CORS) 开发时可以打开，生产环境请根据需要配置 默认注释掉
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# 用于 session 管理（简单的本地会话）
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'change-me-locally')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = ZIP_MAX_SIZE


@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json() or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()

        if not username or not password:
            return jsonify({'code': 1, 'desc': '用户名或密码不能为空'}), 400

        users = load_users()
        matched = None
        for u in users:
            # 支持用 id 或 name 登录
            if username == u.get('id') or username == u.get('name'):
                matched = u
                break

        if not matched or matched.get('password') != password:
            return jsonify({'code': 2, 'desc': '用户名或密码错误'}), 401

        # 成功，写入 session，包含 role
        from flask import session
        session['user'] = {
            'id': matched.get('id'),
            'name': matched.get('name'),
            'role': matched.get('role', 'user')
        }
        return jsonify({'code': 0, 'desc': '登录成功', 'user': session['user']})
    except Exception as e:
        return jsonify({'code': 3, 'desc': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def api_logout():
    from flask import session
    session.pop('user', None)
    return jsonify({'code': 0, 'desc': '已登出'})


@app.route('/api/me', methods=['GET'])
def api_me():
    from flask import session
    user = session.get('user')
    if user:
        return jsonify({'code': 0, 'user': user})
    return jsonify({'code': 1, 'desc': '未登录'}), 401


# 用户管理接口
@app.route('/api/contests/delete', methods=['POST'])
def api_delete_contest():
    data = request.get_json() or {}
    contest_id = (data.get('id') or '').strip()
    if not contest_id:
        return jsonify({'code': 1, 'desc': '缺少项目ID'}), 400
    contest_dir = os.path.join(BASE_DIR, contest_id)
    if not os.path.exists(contest_dir):
        return jsonify({'code': 2, 'desc': '项目不存在'}), 404
    try:
        shutil.rmtree(contest_dir)
    except Exception as e:
        return jsonify({'code': 3, 'desc': f'删除失败: {str(e)}'}), 500
    return jsonify({'code': 0, 'desc': '删除成功'})
@app.route('/api/users/delete', methods=['POST'])
def api_delete_user():
    data = request.get_json() or {}
    user_id = (data.get('id') or '').strip()
    if not user_id:
        return jsonify({'code': 1, 'desc': '缺少用户ID'}), 400
    users = load_users()
    new_users = [u for u in users if u.get('id') != user_id]
    if len(new_users) == len(users):
        return jsonify({'code': 2, 'desc': '用户不存在'}), 404
    with open(os.path.join( 'users.json'), 'w', encoding='utf-8') as f:
        json.dump(new_users, f, ensure_ascii=False, indent=2)
    return jsonify({'code': 0, 'desc': '删除成功'})
@app.route('/api/users', methods=['GET'])
def api_users():
    users = load_users()
    # 不返回密码
    for u in users:
        u.pop('password', None)
    return jsonify(users)

@app.route('/api/users/add', methods=['POST'])
def api_add_user():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    password = (data.get('password') or '').strip()
    role = (data.get('role') or 'user').strip()
    if not name or not password or role not in ['user', 'admin']:
        return jsonify({'code': 1, 'desc': '信息不完整或角色错误'}), 400
    users = load_users()
    # 检查重名
    for u in users:
        if name == u.get('name'):
            return jsonify({'code': 2, 'desc': '用户名已存在'}), 400
    new_id = f"u{str(len(users)+1).zfill(3)}"
    users.append({
        'id': new_id,
        'name': name,
        'password': password,
        'role': role
    })
    # 保存
    with open(os.path.join('users.json'), 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    return jsonify({'code': 0, 'desc': '添加成功'})



# ===================== 健康检查接口 =====================
@app.route('/health', methods=['GET'])
def health():
    """
    健康检查端点 - 返回系统状态
    
    返回:
        {
            'status': 'healthy' 或 'degraded',
            'timestamp': ISO 时间戳,
            'queue_size': 当前队列中的任务数,
            'docker': Docker 连接状态,
            'uptime': 系统运行时间（秒）
        }
    """
    try:
        docker_stats = get_docker_stats()
        docker_status = docker_stats.get('status', 'error')
        # 获取磁盘剩余空间（针对 BASE_DIR 所在分区）
        try:
            disk_free_bytes = get_disk_free_bytes(BASE_DIR)
            disk_free_gb = disk_free_bytes / 1024.0 / 1024.0 / 1024.0 if disk_free_bytes is not None else None
        except Exception:
            disk_free_bytes = None
            disk_free_gb = None

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'queue_size': queue_size(),
            'docker': docker_status,
            'docker_details': {
                'images': docker_stats.get('images_count', 0),
                'containers': docker_stats.get('containers_count', 0),
                'running': docker_stats.get('running_containers', 0),
                'dangling_images': docker_stats.get('dangling_images', 0)
            },
            'disk_free_bytes': disk_free_bytes,
            'disk_free_gb': round(disk_free_gb, 2) if disk_free_gb is not None else None
        }), 200
        
    except Exception as e:
        logger.error(f'Health check error: {str(e)}')
        return jsonify({
            'status': 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 200  # 返回 200，因为这是健康检查端点




@app.route('/create', methods=['GET', 'POST'])
def create_contest():
    """算法创建页面和提交处理"""
    
    # POST 请求处理
    temp_files = []  # 记录临时文件用于清理
    try:
        # 验证表单数据
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title:
            return jsonify({'error': '算法标题不能为空'}), 400
        
        if not description:
            return jsonify({'error': '算法描述不能为空'}), 400

        # 同名校验：不允许已有同名的算法（按 title 忽略大小写匹配）
        try:
            for item in os.listdir(BASE_DIR):
                info_file_path = os.path.join(BASE_DIR, item, 'info', 'info.json')
                if not os.path.exists(info_file_path):
                    continue
                try:
                    with open(info_file_path, 'r', encoding='utf-8') as _f:
                        existing = json.load(_f)
                        existing_title = (existing.get('title') or '').strip()
                        if existing_title and existing_title.lower() == title.lower():
                            return jsonify({'error': '已存在同名算法，请使用不同的标题'}), 400
                except Exception:
                    # 忽略单条读取失败，继续检查其它条目
                    continue
        except Exception:
            # 若遍历出错，不阻止创建；但是记录日志（不抛出）
            try:
                logger.exception('同名校验失败')
            except Exception:
                pass

        # 检查磁盘剩余空间，低于 10GB 则拒绝创建
        try:
            min_bytes = 10 * 1024 ** 3  # 10GB
            sufficient, space_free = is_disk_space_sufficient(BASE_DIR, min_bytes)
            if not sufficient:
                # space_free 应为 int（字节）或 None（但若 None 则 sufficient 为 True）
                return jsonify({'error': f'磁盘可用空间不足（<10GB），当前可用 {space_free / 1024 / 1024 / 1024:.2f} GB'}), 400
        except Exception:
            # 读取磁盘空间异常时记录但不阻止创建
            try:
                logger.exception('检查磁盘剩余空间时出错')
            except Exception:
                pass
        
        # 检查文件
        if 'image' not in request.files:
            return jsonify({'error': '没有上传评测镜像文件'}), 400
        
        if 'source' not in request.files:
            return jsonify({'error': '没有上传评测数据源文件'}), 400
        if 'result' not in request.files:
            return jsonify({'error': '没有上传结果集文件'}), 400

        image_file = request.files['image']
        source_file = request.files['source']
        result_file = request.files['result']

        if image_file.filename == '':
            return jsonify({'error': '镜像文件名为空'}), 400
        if source_file.filename == '':
            return jsonify({'error': '评测数据源文件名为空'}), 400
        if result_file.filename == '':
            return jsonify({'error': '结果集文件名为空'}), 400

        # if not allowed_tar_file(image_file.filename):
        #     return jsonify({'error': '评测镜像只支持 .tar 文件'}), 400
        if not allowed_zip_file(source_file.filename):
            return jsonify({'error': '评测数据源只支持 .zip 文件'}), 400
        if not allowed_zip_file(result_file.filename):
            return jsonify({'error': '结果集只支持 .zip 文件'}), 400

        # 检查 ZIP 文件大小（500MB 限制）
        source_file.seek(0, os.SEEK_END)
        source_size = source_file.tell()
        source_file.seek(0)
        result_file.seek(0, os.SEEK_END)
        result_size = result_file.tell()
        result_file.seek(0)

        if source_size > ZIP_MAX_SIZE:
            return jsonify({'error': f'评测数据源文件过大（最大 {ZIP_MAX_SIZE / 1024 / 1024:.1f }MB，当前 {source_size / 1024 / 1024:.1f}MB）'}), 400
        if result_size > ZIP_MAX_SIZE:
            return jsonify({'error': f'结果集文件过大（最大 {ZIP_MAX_SIZE / 1024 / 1024:.1f }MB，当前 {result_size / 1024 / 1024:.1f}MB）'}), 400

        # 生成算法ID
        contest_id = generate_contest_id()

        # 创建目录结构: {BASE_DIR}/{contest_id}/info/
        contest_dir = os.path.join(BASE_DIR, contest_id)
        info_dir = os.path.join(contest_dir, 'info')
        dataset_source_dir = os.path.join(info_dir, 'dataset', 'source')
        dataset_result_dir = os.path.join(info_dir, 'dataset', 'result')

        os.makedirs(dataset_source_dir, exist_ok=True)
        os.makedirs(dataset_result_dir, exist_ok=True)

        # 检查并保存评测镜像（检查大小限制）
        try:
            image_file.seek(0, os.SEEK_END)
            image_size = image_file.tell()
            image_file.seek(0)
        except Exception:
            image_size = None

        if image_size is not None and image_size > TAR_MAX_SIZE:
            return jsonify({'error': f'评测镜像文件过大（最大 {TAR_MAX_SIZE / 1024 / 1024:.1f}MB，当前 {image_size / 1024 / 1024:.1f}MB）'}), 400

        image_filename = secure_filename(image_file.filename)
        image_tar_path = os.path.join(info_dir, image_filename)
        image_file.save(image_tar_path)
        temp_files.append(image_tar_path)

        # 保存并解压评测数据源
        source_zip_filename = secure_filename(source_file.filename)
        source_zip_path = os.path.join(UPLOAD_FOLDER, f'{contest_id}_source.zip')
        source_file.save(source_zip_path)
        temp_files.append(source_zip_path)

        success, error = extract_zip_to_folder(source_zip_path, dataset_source_dir)
        if not success:
            raise Exception(f'评测数据源解压失败: {error}')

        # 保存并解压结果集
        result_zip_filename = secure_filename(result_file.filename)
        result_zip_path = os.path.join(UPLOAD_FOLDER, f'{contest_id}_result.zip')
        result_file.save(result_zip_path)
        temp_files.append(result_zip_path)

        success, error = extract_zip_to_folder(result_zip_path, dataset_result_dir)
        if not success:
            raise Exception(f'结果集解压失败: {error}')
        
        owner_id = 'system'
        owner_name = '系统'
        try:
            from flask import session
            if session.get('user'):
                owner_id = session['user'].get('id') or owner_id
                owner_name = session['user'].get('name') or owner_name
        except Exception:
            pass

        # 检查封面图文件
        if 'cover_image' not in request.files:
            return jsonify({'error': '没有上传封面图文件'}), 400

        cover_image_file = request.files['cover_image']

        if cover_image_file.filename == '':
            return jsonify({'error': '封面图文件名为空'}), 400

        if not allowed_image_file(cover_image_file.filename):
            return jsonify({'error': '封面图只支持 .jpg 和 .png 文件'}), 400

        # 保存封面图
        cover_image_filename = secure_filename(cover_image_file.filename)
        cover_image_path = os.path.join(info_dir, cover_image_filename)
        cover_image_file.save(cover_image_path)
        temp_files.append(cover_image_path)

        # 创建 info.json 文件
        info_data = {
            'title': title,
            'description': description,
            'image': image_filename,
            'source_dataset': source_zip_filename,
            'result_dataset': result_zip_filename,
            'cover_image': cover_image_filename,  # 添加封面图路径
            'owner_id': owner_id,
            'owner_name': owner_name,
            'createTime': datetime.utcnow().isoformat()
        }
        info_file = os.path.join(info_dir, 'info.json')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info_data, f, ensure_ascii=False, indent=2)
        
        # 清理临时 ZIP 文件
        for temp_file in temp_files:
            try:
                if temp_file.endswith('.zip') and os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        
        return jsonify({
            'status': 'success',
            'message': '算法创建成功',
            'contest_id': contest_id
        }), 201
    
    except Exception as e:
        # 清理临时文件
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                    elif os.path.isdir(temp_file):
                        shutil.rmtree(temp_file)
            except:
                pass
        
        return jsonify({'error': str(e), 'status': 'error'}), 500



@app.route('/api/contests')
def api_contests():
    """API: 获取所有算法信息"""
    contests = get_all_contests()
    return jsonify(contests)


@app.route('/api/upload-config', methods=['GET'])
def api_upload_config():
    """返回前端用于上传验证的服务端配置（允许的后缀和大小限制）。

    返回字段：
      - allowed_tar_extensions: ["tar", "tar.gz", ...]
      - allowed_zip_extensions: ["zip", ...]
      - allowed_image_extensions: ["jpg", "png", ...]
      - tar_max_size: 最大 tar 文件大小（字节）
      - zip_max_size: 最大 zip 文件大小（字节）
      - image_max_size: 最大图片文件大小（字节）
    """
    try:
        # 从 config 中读取允许的扩展名集合（可能为 set）并序列化为列表
        from config import ALLOWED_TAR_EXTENSIONS, ALLOWED_ZIP_EXTENSIONS, TAR_MAX_SIZE, IMAGE_MAX_SIZE

        allowed_tar = list(ALLOWED_TAR_EXTENSIONS) if ALLOWED_TAR_EXTENSIONS else []
        allowed_zip = list(ALLOWED_ZIP_EXTENSIONS) if ALLOWED_ZIP_EXTENSIONS else []

        # 图片扩展使用默认集合
        allowed_image = ['jpg', 'png']

        # 大小限制：从配置中读取
        tar_max = TAR_MAX_SIZE
        zip_max = ZIP_MAX_SIZE
        image_max = IMAGE_MAX_SIZE

        return jsonify({
            'allowed_tar_extensions': allowed_tar,
            'allowed_zip_extensions': allowed_zip,
            'allowed_image_extensions': allowed_image,
            'tar_max_size': tar_max,
            'zip_max_size': zip_max,
            'image_max_size': image_max
        })
    except Exception as e:
        logger.exception('无法读取上传配置')
        return jsonify({'error': str(e)}), 500


@app.route('/api/disk-info', methods=['GET'])
def api_disk_info():
    """返回 BASE_DIR 所在分区的磁盘总量与可用量（字节）。

    返回字段：total_bytes, free_bytes, free_percent（0-100）
    """
    try:
        usage = shutil.disk_usage(BASE_DIR)
        total = usage.total
        free = usage.free
        percent = round((free / total) * 100, 2) if total else None
        return jsonify({'total_bytes': total, 'free_bytes': free, 'free_percent': percent})
    except Exception as e:
        logger.exception('无法读取磁盘信息')
        return jsonify({'error': str(e)}), 500

@app.route('/api/contests/<contest_id>/submissions')
def api_contest_submissions(contest_id):
    """API: 获取某算法的所有提交（参赛者ID、姓名、提交时间、主办方结果）"""
    try:
        submissions = get_contest_submissions(contest_id)
        return jsonify(submissions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # 获取算法ID
        unique_id = request.form.get('unique_id', '').strip()
        if not unique_id:
            return jsonify({'error': '算法ID不能为空'}), 400
        
        # 参赛者ID（可选，优先使用已登录用户的 session 中的 id）
        participant_id = (request.form.get('participant_id') or '').strip()
        try:
            from flask import session
            if session.get('user'):
                # 强制使用登录用户 id，防止伪造
                participant_id = session['user'].get('id')
        except Exception:
            pass

        # 验证 participant_id（允许空则使用 default 目录；若非空必须满足白名单）
        if participant_id:
            if not re.match(r'^[A-Za-z0-9_-]{1,64}$', participant_id):
                return jsonify({'error': '非法的 participant_id'}), 400

        # 检查文件
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        if not allowed_tar_file(file.filename):
            return jsonify({'error': '只支持 .tar,.tar.gz 文件'}), 400
        
        # 验证算法是否存在且包含数据源
        contest_dir = os.path.join(BASE_DIR, unique_id)
        info_dir = os.path.join(contest_dir, 'info')
        dataset_source_dir = os.path.join(info_dir, 'dataset', 'source')
        
        if not os.path.exists(dataset_source_dir):
            return jsonify({'error': f'算法 {unique_id} 的数据源不存在'}), 400

        # 在提交前检查磁盘剩余空间，低于 10GB 则拒绝提交
        try:
            min_bytes = 10 * 1024 ** 3  # 10GB
            sufficient, space_free = is_disk_space_sufficient(BASE_DIR, min_bytes)
            if not sufficient:
                return jsonify({'error': f'服务器磁盘可用空间不足（<10GB），当前可用 {space_free / 1024 / 1024 / 1024:.2f} GB'}), 400
        except Exception:
            try:
                logger.exception('检查磁盘剩余空间时出错')
            except Exception:
                pass
        
        # 创建目录结构: {BASE_DIR}/{ID}/evaluation/submissions
        _, evaluation_dir, submissions_root, submissions_json_path = contest_paths(unique_id)
        os.makedirs(submissions_root, exist_ok=True)
        
        # 方案 A：为每次提交创建独立目录 submission_{timestamp}
        submission_timestamp = str(int(time.time() * 1000))  # 毫秒级时间戳
        submission_dir = os.path.join(submissions_root, f'submission_{submission_timestamp}')
        os.makedirs(submission_dir, exist_ok=True)
        
        # 保存上传的文件到本次提交目录
        filename = secure_filename(file.filename)
        image_tar_path = os.path.join(submission_dir, filename)
        # 检查上传 tar 大小限制
        try:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
        except Exception:
            file_size = None

        try:
            from config import TAR_MAX_SIZE
        except Exception:
            TAR_MAX_SIZE = ZIP_MAX_SIZE

        if file_size is not None and file_size > TAR_MAX_SIZE:
            return jsonify({'error': f'上传文件过大（最大 {TAR_MAX_SIZE/1024/1024:.1f}MB，当前 {file_size/1024/1024:.1f}MB）'}), 400

        file.save(image_tar_path)

        # 创建输出目录（用于容器挂载），放在本次提交目录下
        output_dir = os.path.join(submission_dir, 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 创建输入目录，并复制数据源到该目录
        input_dir = os.path.join(submission_dir, 'input')
        if os.path.exists(input_dir):
            shutil.rmtree(input_dir)
        os.makedirs(input_dir, exist_ok=True)

        # 复制 dataset/source 下的所有文件到本次提交的 input
        for item in os.listdir(dataset_source_dir):
            src = os.path.join(dataset_source_dir, item)
            dst = os.path.join(input_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        
        # 记录本次提交到 submissions.json（参赛者提交历史），设置排队状态
        try:
            output_rel_path = normalize_rel_path(output_dir, contest_dir)
            submission_record = {
                'submission_id': submission_timestamp,
                'timestamp': datetime.fromtimestamp(int(submission_timestamp) / 1000).isoformat(),
                'status_code': 'QUEUED',
                'status_desc': '已进入评测队列',
                'participant_id': participant_id,
                'storage_path': os.path.relpath(submission_dir, start=contest_dir),
                'output_path': output_rel_path
            }
            append_submission_record(unique_id, submission_record)
        except Exception as e:
            print(f"Failed to save submission record: {str(e)}")

        # 将任务加入本地队列
        queue_len = enqueue_task({
            'submission_id': submission_timestamp,
            'contest_id': unique_id,
            'participant_id': participant_id,
            'image_tar_path': image_tar_path,
            'output_dir': output_dir,
            'input_dir': input_dir,
            'contest_dir': contest_dir,
            'submission_dir': submission_dir
        })
        
        return jsonify({
            'code': 0,
            'desc': '已进入评测队列',
            'participant_id': participant_id,
            'submission_time': submission_timestamp,
            'submission_id': submission_timestamp,
            'queue_size': queue_len,
            'queue_ahead': max(queue_len - 1, 0)
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status_code': 'ERROR'}), 500


# Vue 历史路由的兜底（一定要放最后）
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def vue_app(path):
    # 绝对路径
    real_path = os.path.join(STATIC_ROOT, path)

    # 1. try_files $uri  —— 如果是静态文件
    if os.path.isfile(real_path):
        return send_from_directory(STATIC_ROOT, path)

    # 2. try_files $uri/  —— 如果是目录，尝试目录下的 index.html
    index_html_path = os.path.join(real_path, "index.html")
    if os.path.isfile(index_html_path):
        return send_from_directory(real_path, "index.html")

    # 3. 全部 fallback 到 /index.html（Vue history mode）
    return send_from_directory(STATIC_ROOT, "index.html")


if __name__ == '__main__':
    # 启动队列处理线程
    queue_thread = threading.Thread(target=run_queue_worker, daemon=True)
    queue_thread.start()
    logger.info("Queue worker started")
    
    # 启动 Docker 资源清理线程
    cleanup_thread = threading.Thread(
        target=periodic_cleanup,
        kwargs={'interval_hours': 1},  # 每小时清理一次
        daemon=True
    )
    cleanup_thread.start()
    logger.info("Docker cleanup scheduler started")
    
    logger.info("Application starting on http://0.0.0.0:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)

