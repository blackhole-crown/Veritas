import os
import sys
from celery import Celery
import logging
from dotenv import load_dotenv

# 加载 api 目录下的 .env 文件
api_dir = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(api_dir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery('veritas')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
RESULT_DIR = os.path.join(PROJECT_ROOT, 'celery_results')
os.makedirs(RESULT_DIR, exist_ok=True)

logger.info(f"Celery results directory: {RESULT_DIR}")

# 从环境变量读取 Redis 配置
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_DB = os.environ.get('REDIS_DB', '0')

celery_app.conf.update(
    broker_url=f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
    result_backend='file://' + RESULT_DIR,
    
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    task_track_started=True,
    task_annotations={
        '*': {
            'max_retries': 3,
            'retry_backoff': True,
            'retry_backoff_max': 700,
            'retry_jitter': False
        }
    },
    
    result_expires=86400,
    
    result_backend_transport_options={
        'data_folder': RESULT_DIR,
        'taskmeta_filename': 'taskmeta.json'
    },
    
    imports=['tasks']
)


@celery_app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')