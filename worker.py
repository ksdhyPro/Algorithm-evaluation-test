import docker
import os
import json
import threading
import time
from enum import Enum
from config import (
    PARTICIPANT_TIMEOUT, 
    PARTICIPANT_CPU_CORES, 
    PARTICIPANT_MEM_LIMIT,
    ORGANIZER_TIMEOUT, 
    ORGANIZER_CPU_CORES, 
    ORGANIZER_MEM_LIMIT
)
from container_metrics import ContainerMetricsCollector
from rules.organizer_rules import validate_organizer_results, OrganizerValidationError, add_runtime_info

class StatusCode(Enum):
    SUCCESS = "SUCCESS"  # 执行成功
    TIMEOUT = "TIMEOUT"  # 超时
    ERROR = "ERROR"  # 执行出错
    CONTAINER_ERROR = "CONTAINER_ERROR"  # 容器执行失败

def run_worker(image_tar_path: str, output_dir: str, input_dir: str = None, contest_dir: str = None, timeout: int = None, participant_id: str = None):
    # 使用配置中的超时时间作为默认值
    if timeout is None:
        timeout = PARTICIPANT_TIMEOUT
    
    client = docker.from_env()
    container = None
    image = None
    organizer_container = None
    organizer_image = None
    logs_text = ""
    status_code = StatusCode.ERROR
    organizer_output_abs = None
    
    # 参赛者容器统计
    metrics_collector = None
    participant_runtime = 0  # 运行时间（秒）
    
    try:
        # 加载镜像
        with open(image_tar_path, 'rb') as f:
            image = client.images.load(f.read())[0]

        # 创建输出挂载目录（使用绝对路径，Windows Docker 需要）
        output_dir_abs = os.path.abspath(output_dir)
        os.makedirs(output_dir_abs, exist_ok=True)

        # 准备挂载卷
        volumes = {output_dir_abs: {'bind': '/output', 'mode': 'rw'}}
        
        # 挂载评测数据源 source 到 /input
        if contest_dir:
            source_dir = os.path.join(contest_dir, 'info', 'dataset', 'source')
            source_dir_abs = os.path.abspath(source_dir)
            if os.path.exists(source_dir_abs):
                volumes[source_dir_abs] = {'bind': '/input', 'mode': 'ro'}

        # 运行容器（使用镜像默认命令）
        container = client.containers.run(
            image=image.id,
            detach=True,
            volumes=volumes,
            network_disabled=True,
            mem_limit=PARTICIPANT_MEM_LIMIT,
            nano_cpus=PARTICIPANT_CPU_CORES * 1_000_000_000,
            user='root'
        )

        # 启动参赛者容器的资源指标收集
        # 使用更短的采样间隔以便快速任务也能收集到数据
        metrics_collector = ContainerMetricsCollector(container.id, collection_interval=0.2)
        metrics_thread = metrics_collector.start_collection()
        
        # 记录开始时间
        start_time = time.time()

        # 等待容器执行完成（带超时检测）
        def wait_container():
            try:
                result = container.wait()
                exit_code = result.get('StatusCode', -1)
                return result, exit_code
            except Exception as e:
                return None, -1
        
        # 使用线程等待容器完成
        wait_result = [None]
        wait_exit_code = [-1]
        
        def wait_thread():
            result, exit_code = wait_container()
            wait_result[0] = result
            wait_exit_code[0] = exit_code
        
        wait_thread_obj = threading.Thread(target=wait_thread)
        wait_thread_obj.daemon = True
        wait_thread_obj.start()
        wait_thread_obj.join(timeout=timeout)
        
        # 计算运行时间
        participant_runtime = round(time.time() - start_time, 2)
        
        # 给采集线程一点额外的时间来完成最后的采样
        # 特别是对于快速完成的容器，这确保了至少有一次有效采样
        time.sleep(0.1)
        
        # 停止指标收集
        metrics_collector.stop_collection()
        
        # 收集容器运行日志（在停止容器前收集，确保能获取到日志）
        try:
            logs = container.logs(stdout=True, stderr=True, timestamps=False)
            logs_text = logs.decode('utf-8', errors='replace')
        except Exception:
            logs_text = "获取日志失败"
        
        # 检查是否超时
        if wait_thread_obj.is_alive():
            # 超时，强制停止容器
            try:
                container.stop(timeout=10)
            except Exception:
                pass
            exit_code = -1
            status_code = StatusCode.TIMEOUT
        else:
            # 正常完成
            result = wait_result[0]
            exit_code = wait_exit_code[0]
            if exit_code == 0:
                # 检查是否输出了 result.json 文件predict_results
                result_json_path = os.path.join(output_dir_abs, 'results.json')
                if os.path.exists(result_json_path):
                    status_code = StatusCode.SUCCESS
                else:
                    # 容器退出码为0但没有输出result.json，视为失败
                    status_code = StatusCode.CONTAINER_ERROR
                    if logs_text and "获取日志失败" not in logs_text:
                        logs_text += "\n错误: 容器执行完成但未找到 results.json 文件"
                    else:
                        logs_text = "错误: 容器执行完成但未找到 results.json 文件"
            else:
                status_code = StatusCode.CONTAINER_ERROR

        # -- 在参赛者容器执行完成后，尝试运行主办方镜像（如果提供 contest_dir 并且 info.json 指定了 image）
        organizer_result = None
        if contest_dir:
            try:
                info_json_path = os.path.join(contest_dir, 'info', 'info.json')
                if os.path.exists(info_json_path):
                    with open(info_json_path, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    org_image_filename = info.get('image')
                    if org_image_filename:
                        org_image_tar = os.path.join(contest_dir, 'info', org_image_filename)
                        if os.path.exists(org_image_tar):
                            # 准备 organizer 输出目录（写入到本次提交目录下的 organizer_output）
                            # output_dir_abs 是参赛者的 output（submission/.../output），我们在同级目录下创建 organizer_output
                            organizer_output_abs = os.path.join(os.path.dirname(output_dir_abs), 'organizer_output')
                            organizer_output_abs = os.path.abspath(organizer_output_abs)
                            os.makedirs(organizer_output_abs, exist_ok=True)

                            # 加载主办方镜像
                            with open(org_image_tar, 'rb') as f:
                                organizer_image = client.images.load(f.read())[0]


                            # 挂载评测结果集 result 到 /result，参赛者 output -> /input，主办方 output -> /output
                            participant_output_abs = output_dir_abs
                            result_dir = os.path.join(contest_dir, 'info', 'dataset', 'result')
                            result_dir_abs = os.path.abspath(result_dir)
                            org_volumes = {
                                participant_output_abs: {'bind': '/input', 'mode': 'ro'},
                                organizer_output_abs: {'bind': '/output', 'mode': 'rw'}
                            }
                            if os.path.exists(result_dir_abs):
                                org_volumes[result_dir_abs] = {'bind': '/result', 'mode': 'ro'}

                            # 运行主办方容器
                            organizer_container = client.containers.run(
                                image=organizer_image.id,
                                detach=True,
                                volumes=org_volumes,
                                network_disabled=True,
                                mem_limit=ORGANIZER_MEM_LIMIT,
                                nano_cpus=ORGANIZER_CPU_CORES * 1_000_000_000,
                                user='root'
                            )

                            # 等待主办方容器完成（同步等待，沿用 timeout）
                            try:
                                org_wait = organizer_container.wait(timeout=timeout)
                                org_exit = org_wait.get('StatusCode', -1)
                            except Exception:
                                try:
                                    organizer_container.stop(timeout=5)
                                except Exception:
                                    pass
                                org_exit = -1

                            # 获取主办方日志
                            try:
                                org_logs = organizer_container.logs(stdout=True, stderr=True, timestamps=False)
                                org_logs_text = org_logs.decode('utf-8', errors='replace')
                            except Exception:
                                org_logs_text = '获取主办方日志失败'

                            organizer_result = {
                                'exit_code': org_exit,
                                'logs': org_logs_text
                            }
                        else:
                            organizer_result = {'error': f'主办方镜像文件未找到: {org_image_tar}'}
                else:
                    organizer_result = {'error': 'info.json 未找到，无法运行主办方镜像'}
            except Exception as e:
                organizer_result = {'error': f'运行主办方镜像失败: {str(e)}'}

    except Exception as e:
        # 打印完整回溯以便定位错误来源（例如 Docker API 连接超时）
        import traceback
        traceback.print_exc()
        print("Exception type:", type(e), e)
        status_code = StatusCode.ERROR
        # 把回溯也放入返回的 logs_text，便于上层日志查看
        logs_text = f"执行出错: {str(e)}\nTraceback:\n{traceback.format_exc()}"

    finally:
        # 清理容器和镜像
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass
        if image:
            try:
                client.images.remove(image.id, force=True)
            except Exception:
                pass
        # 清理主办方容器和镜像
        if organizer_container:
            try:
                organizer_container.remove(force=True)
            except Exception:
                pass
        if organizer_image:
            try:
                client.images.remove(organizer_image.id, force=True)
            except Exception:
                pass
    
    # 将 StatusCode 映射为数字 code 和描述 desc
    code_map = {
        StatusCode.SUCCESS: (0, '参赛镜像执行成功'),
        StatusCode.TIMEOUT: (1, '参赛镜像执行超时'),
        StatusCode.CONTAINER_ERROR: (2, '参赛镜像容器执行失败'),
        StatusCode.ERROR: (3, '执行出错')
    }

    code, desc = code_map.get(status_code, (3, '执行出错'))

    # 参赛者镜像的相对路径（相对于 contest_dir，如果未提供则为文件名）
    try:
        if contest_dir:
            participant_image_rel = os.path.relpath(image_tar_path, start=contest_dir)
        else:
            participant_image_rel = os.path.basename(image_tar_path)
    except Exception:
        participant_image_rel = os.path.basename(image_tar_path)

    # 主办方日志与 results.json 内容
    organizer_logs = None
    organizer_results = None
    try:
        if 'organizer_result' in locals() and organizer_result is not None:
            organizer_logs = organizer_result.get('logs') if isinstance(organizer_result, dict) else None

        # 尝试读取主办方生成的 results.json，从本次提交的 organizer_output 目录读取
        candidate_paths = []
        if organizer_output_abs:
            candidate_paths.append(os.path.join(organizer_output_abs, 'results.json'))

        for result_json_path in candidate_paths:
            if result_json_path and os.path.exists(result_json_path):
                try:
                    # 使用校验规则模块验证主办方结果
                    organizer_results = validate_organizer_results(result_json_path)
                    
                    # 验证通过，获取参赛者容器的资源指标
                    participant_metrics = {}
                    if metrics_collector:
                        # 确保数据被正确采集
                        participant_metrics = metrics_collector.get_summary()
                        print(f"[WORKER] 采集到的指标: {participant_metrics}")
                    else:
                        print(f"[WORKER] metrics_collector 为 None")
                    
                    print(f"[WORKER] 运行时间: {participant_runtime}s")
                    
                    # 添加运行时信息到结果
                    organizer_results = add_runtime_info(organizer_results, participant_metrics, participant_runtime, debug=True)
                    
                    # 保存回文件
                    with open(result_json_path, 'w', encoding='utf-8') as wf:
                        json.dump(organizer_results, wf, ensure_ascii=False, indent=2)
                            
                except OrganizerValidationError as ve:
                    # 格式验证失败
                    organizer_results = None
                    # 标记为主办方评测失败
                    status_code = StatusCode.CONTAINER_ERROR
                    code, _ = code_map.get(status_code, (3, '执行出错'))
                    if organizer_logs:
                        organizer_logs += f"\n主办方结果验证失败: {str(ve)}"
                    else:
                        organizer_logs = f"主办方结果验证失败: {str(ve)}"
                except Exception:
                    try:
                        with open(result_json_path, 'r', encoding='utf-8', errors='replace') as rf:
                            organizer_results = rf.read()
                    except Exception:
                        organizer_results = None
                break
    except Exception:
        pass

    result_dict = {
        'code': code,
        'desc': desc,
        'participant_logs': logs_text,
        'participant_image': participant_image_rel,
        'organizer_logs': organizer_logs,
        'organizer_results': organizer_results,
        'participant_id': participant_id
    }

    return result_dict


if __name__ == '__main__':
    run_worker(
        image_tar_path='app2.tar',
        output_dir='./projects'
        # timeout 将使用 config.py 中的 PARTICIPANT_TIMEOUT 配置
    )
