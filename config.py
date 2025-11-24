import os
from dotenv import load_dotenv

# 加载 .env 文件
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path, override=True)

# 基础配置
BASE_DIR = os.getenv('BASE_DIR', './projects')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
ALLOWED_TAR_EXTENSIONS = set(os.getenv('ALLOWED_TAR_EXTENSIONS', 'tar,tar.gz').split(','))
ALLOWED_ZIP_EXTENSIONS = set(os.getenv('ALLOWED_ZIP_EXTENSIONS', 'zip').split(','))
ZIP_MAX_SIZE = int(os.getenv('ZIP_MAX_SIZE', '524288000'))

# 最大 tar 文件大小（字节），默认与 ZIP_MAX_SIZE 相同（500MB）
TAR_MAX_SIZE = int(os.getenv('TAR_MAX_SIZE', '524288000'))

# 封面图最大文件大小（字节），默认 5MB
IMAGE_MAX_SIZE = int(os.getenv('IMAGE_MAX_SIZE', str(5 * 1024 * 1024)))

# 参赛方（Participant）评测配置
PARTICIPANT_TIMEOUT = int(os.getenv('PARTICIPANT_TIMEOUT', '300'))
PARTICIPANT_CPU_CORES = int(os.getenv('PARTICIPANT_CPU_CORES', '2'))
PARTICIPANT_MEM_LIMIT = os.getenv('PARTICIPANT_MEM_LIMIT', '2g')

# 主办方（Organizer）评测配置
ORGANIZER_TIMEOUT = int(os.getenv('ORGANIZER_TIMEOUT', '300'))
ORGANIZER_CPU_CORES = int(os.getenv('ORGANIZER_CPU_CORES', '1'))
ORGANIZER_MEM_LIMIT = os.getenv('ORGANIZER_MEM_LIMIT', '1g')
