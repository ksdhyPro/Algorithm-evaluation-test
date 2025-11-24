"""应用程序通用的工具函数集合。

本模块提供一组轻量级的帮助函数，包括：
- 从磁盘加载用户列表
- 解压 ZIP 文件到目录
- 简单的文件名/后缀校验
- 路径归一化（生成相对路径并统一为 POSIX 风格）
- 读取结果文件（优先解析为 JSON，否则返回原始文本）
- 获取并判断磁盘可用空间

这些函数尽量保持副作用最小、容错友好，以避免在运行时因为单个文件出错而导致整个服务中断。
"""

import json
import os
import zipfile
import shutil

from config import ALLOWED_TAR_EXTENSIONS, ALLOWED_ZIP_EXTENSIONS


def load_users():
    """从仓库根目录下的 `users.json` 加载并返回用户列表。

    若文件不存在或解析失败，返回空列表。该函数对错误保持宽容，
    以避免因用户存储丢失或损坏导致应用崩溃。
    """
    users_path = os.path.join(os.path.dirname(__file__), 'users.json')
    if not os.path.exists(users_path):
        return []
    try:
        with open(users_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def extract_zip_to_folder(zip_path, extract_path):
    """将 ZIP 压缩包解压到目标目录。

    返回 (success: bool, error: str|None)。解压成功时返回 (True, None)，
    失败时返回 (False, 错误信息)。
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        return True, None
    except Exception as e:
        return False, str(e)


def allowed_tar_file(filename):
    """判断给定文件名是否为允许的 tar 扩展名。
    
    使用配置中的 `ALLOWED_TAR_EXTENSIONS` 进行校验。
    支持多级扩展名如 tar.gz
    """
    if not '.' in filename:
        return False
    
    # 获取文件的所有可能扩展名（从右往左）
    parts = filename.lower().split('.')
    possible_extensions = []
    
    # 生成所有可能的扩展名组合（不带点）
    for i in range(1, len(parts)):
        extension = '.'.join(parts[i:])
        possible_extensions.append(extension)
    
    # 检查是否有匹配的扩展名
    for ext in possible_extensions:
        if ext in ALLOWED_TAR_EXTENSIONS:
            return True
    
    return False


def allowed_zip_file(filename):
    """判断给定文件名是否为允许的 zip 扩展名。

    使用配置中的 `ALLOWED_ZIP_EXTENSIONS` 进行校验。
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_ZIP_EXTENSIONS


def allowed_image_file(filename):
    """判断给定文件名是否为允许的图片类型（jpg/png）。"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'png'}


def normalize_rel_path(path, base):
    """将文件系统路径规范化为相对于 `base` 的 POSIX 风格相对路径。

    行为说明：
    - 如果 `path` 是空值，返回 None。
    - 尝试计算从 `base` 到 `path` 的相对路径，失败时回退到原始路径。
    - 将反斜杠替换为正斜杠，便于在 JSON/前端中一致显示。
    """
    if not path:
        return None
    try:
        rel_path = os.path.relpath(path, start=base)
    except Exception:
        rel_path = path
    return rel_path.replace('\\', '/')


def read_results_file(json_path):
    """读取结果文件并优先尝试解析为 JSON，失败则返回原始文本。

    优先级：
    1. 尝试解析为 JSON 并返回对象；
    2. 若解析失败，尝试以替换错误方式读取并返回原始文本；
    3. 读取失败则返回 None。
    """
    if not json_path or not os.path.exists(json_path):
        return None
    try:
        with open(json_path, 'r', encoding='utf-8') as rf:
            return json.load(rf)
    except Exception:
        try:
            with open(json_path, 'r', encoding='utf-8', errors='replace') as rf:
                return rf.read()
        except Exception:
            return None


def get_disk_free_bytes(path):
    """返回路径 `path` 所在文件系统的可用字节数。

    出错时返回 None（例如权限或 IO 错误）。
    """
    try:
        usage = shutil.disk_usage(path)
        return usage.free
    except Exception:
        return None


def is_disk_space_sufficient(path, min_bytes):
    """检查 `path` 所在分区是否至少有 `min_bytes` 可用空间。

    返回 (sufficient: bool, free_bytes: int|None)。

    设计说明：当无法读取磁盘可用空间信息（返回 None）时，为了兼容
    现有行为，函数会返回 (True, None)，即不阻止调用方继续操作。
    调用方可以根据返回的 free_bytes 决定是否进一步处理或记录告警。
    """
    free = get_disk_free_bytes(path)
    if free is None:
        return True, None
    return (free >= min_bytes), free

