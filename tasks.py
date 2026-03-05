import os
import sys
import logging
from celery_app import celery_app

# 动态添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Main import chat
import psycopg2
# 在现有导入后面添加
from callback_manager import callback_manager
import psycopg2

# 数据库配置（与主应用相同）
DB_CONFIG = {
    'dbname': 'veritas_news',
    'user': 'zhouzehui',
    'host': '139.224.18.139',
    'port': '5433',
    'password': 'zzh050119.'
}

logger = logging.getLogger(__name__)

def get_db_connection():
    """获取数据库连接"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise

def update_result_status(result_id, status, error_message=None):
    """更新任务状态到数据库"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if error_message:
                cursor.execute(
                    "UPDATE Result SET status = %s, error_message = %s WHERE id = %s",
                    (status, error_message, result_id)
                )
            else:
                cursor.execute(
                    "UPDATE Result SET status = %s WHERE id = %s",
                    (status, result_id)
                )
            conn.commit()
            logger.info(f"Updated result {result_id} status to {status}")
    except Exception as e:
        logger.error(f"Failed to update result status: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

@celery_app.task(bind=True, name='tasks.run_chat_task')
def run_chat_task(self, title, result_id):
    """
    Celery 任务：执行验证处理
    """
    task_id = self.request.id
    logger.info(f"Starting Celery chat task {task_id} for title: {title}")
    
    try:
        # 更新状态为处理中
        update_result_status(result_id, 'processing')
        
        # 执行主要的验证逻辑
        chat(title, result_id, None)
        
        # 更新状态为完成
        update_result_status(result_id, 'completed')
        
        logger.info(f"Completed Celery chat task {task_id} for title: {title}")
        
        # ========== 新增：任务完成后触发回调 ==========
        try:
            # 通过result_id查询对应的claim_uuid
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT q.uuid, q.title
                    FROM Query q
                    JOIN Result r ON q.id = r.query_id
                    WHERE r.id = %s
                """, (result_id,))
                result = cursor.fetchone()
                
                if result:
                    claim_uuid, claim_title = result
                    # 发送成功回调
                    callback_manager.send_callback(
                        claim_uuid=str(claim_uuid),
                        task_id=task_id,
                        status='completed',
                        title=claim_title
                    )
                    logger.info(f"Callback triggered for claim {claim_uuid}")
        except Exception as e:
            logger.error(f"Failed to trigger callback for result_id {result_id}: {e}")
        # ============================================
        
        return {
            'status': 'success',
            'result_id': result_id,
            'title': title
        }
        
    except Exception as e:
        error_msg = f"Task failed: {str(e)}"
        logger.error(f"Celery chat task {task_id} failed: {error_msg}", exc_info=True)
        
        # 更新状态为失败
        update_result_status(result_id, 'failed', error_msg)
        
        # ========== 新增：任务失败时也触发回调 ==========
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT q.uuid, q.title
                    FROM Query q
                    JOIN Result r ON q.id = r.query_id
                    WHERE r.id = %s
                """, (result_id,))
                result = cursor.fetchone()
                
                if result:
                    claim_uuid, claim_title = result
                    # 发送失败回调
                    callback_manager.send_callback(
                        claim_uuid=str(claim_uuid),
                        task_id=task_id,
                        status='failed',
                        title=claim_title
                    )
                    logger.info(f"Failure callback triggered for claim {claim_uuid}")
        except Exception as callback_error:
            logger.error(f"Failed to trigger failure callback: {callback_error}")
        # ================================================
        
        # 重新抛出异常，让 Celery 知道任务失败
        raise self.retry(exc=e, countdown=60)