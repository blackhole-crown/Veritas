import os
import sys
from celery import Celery
import logging

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 Celery 实例
celery_app = Celery('veritas')

# 确保结果目录存在 - 放在项目目录下，方便管理
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
RESULT_DIR = os.path.join(PROJECT_ROOT, 'celery_results')
os.makedirs(RESULT_DIR, exist_ok=True)

logger.info(f"Celery results directory: {RESULT_DIR}")

# 配置 Celery - 使用文件系统作为结果后端
celery_app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='file://' + RESULT_DIR,  # 使用文件系统作为结果后端
    
    # 任务相关配置
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 工作进程配置
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # 任务重试策略
    task_track_started=True,
    task_annotations={
        '*': {
            'max_retries': 3,
            'retry_backoff': True,
            'retry_backoff_max': 700,
            'retry_jitter': False
        }
    },
    
    # 结果过期时间（秒）
    result_expires=86400,  # 24小时
    
    # 文件系统后端特定配置
    result_backend_transport_options={
        'data_folder': RESULT_DIR,
        'taskmeta_filename': 'taskmeta.json'
    },
    
    # 添加这一行，明确指定任务模块
    imports=['tasks']
)

# 可选：添加全局错误处理
@celery_app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')