import os
import sys
import psycopg2
from flask import Flask, request, jsonify, Response
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import logging
import time
from uuid import UUID
import json
# 在现有导入后面添加
from callback_manager import callback_manager
# 动态添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import sql, utils
from tasks import run_chat_task  # 导入 Celery 任务

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
K = 5


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

DB_CONFIG = {
    'dbname': 'veritas_news',
    'user': 'zhouzehui', 
    'host': '139.224.18.139',
    'port': '5433',
    'password': 'zzh050119.'
}

def get_db_connection():
    """获取数据库连接"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise

@app.route('/doVeritas', methods=['POST'])
def do_veritas():
    try:
        # 1. 验证输入
        data = request.get_json()
        if not data:
            return jsonify({"status": 400, "message": "Empty request body"}), 400

        title = data.get('title')
        source = data.get('source', '')  # 使用默认值简化
        url = data.get('url', '')
        
        if not title:  # 修正错误信息
            return jsonify({"status": 400, "message": "Title is required"}), 400

        # 2. 插入数据库
        try:
            query_data = sql.insert_query(title, url, source)
            uuid = query_data['uuid']
            query_id = query_data['id']
        except Exception as e:
            logger.error(f"Database insert error: {e}", exc_info=True)
            return jsonify({"status": 500, "message": f"Database error: {str(e)}"}), 500

        # 3. 获取验证结果（同步执行）
        max_retries = 3
        for attempt in range(max_retries):
            try:
                veritas = utils.origin_judge(title, query_data, K)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed after {max_retries} attempts: {e}")
                    veritas = "ERROR"
                else:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                    time.sleep(0.5)
        
        # 4. 创建Result记录
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO Result (title, query_id, status)
                    VALUES (%s, %s, 'pending')
                    RETURNING id
                    """,
                    (title, query_id)
                )
                result_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Created initial Result record with id: {result_id}")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to create Result record: {e}", exc_info=True)
            return jsonify({"status": 500, "message": f"Database error: {str(e)}"}), 500
        finally:
            if conn:
                conn.close()

        # 5. 启动 Celery 后台任务
        task = run_chat_task.apply_async(args=[title, result_id])
        logger.info(f"Started Celery task {task.id} for result_id {result_id}")

        # 6. 检查并注册回调
        callback_url = data.get('callback_url')
        callback_registered = False
        
        if callback_url:
            # 验证回调URL格式
            if not callback_url.startswith(('http://', 'https://')):
                return jsonify({"status": 400, "message": "Invalid callback URL format"}), 400
            
            callback_registered = callback_manager.register_callback(
                str(uuid), callback_url
            )
            logger.info(f"Callback registered for claim {uuid}: {callback_url}")

        # 7. 返回即时结果
        response_data = {
            "claim": str(uuid),
            "veritas": veritas,
            "task_id": task.id,
            "callback_registered": callback_registered
        }

        if callback_registered:
            response_data["callback_url"] = callback_url

        return Response(
            json.dumps({
                "status": 200,
                "message": "OK",
                "data": response_data
            }, ensure_ascii=False),
            mimetype='application/json; charset=utf-8',
            status=200
        )

    except Exception as e:
        logger.exception("Unexpected error in doVeritas")
        return jsonify({"status": 500, "message": f"Internal server error: {str(e)}"}), 500


# 添加任务状态查询接口
@app.route('/taskStatus/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """查询 Celery 任务状态"""
    from celery_app import celery_app
    
    task_result = celery_app.AsyncResult(task_id)
    
    
    response = {
        'task_id': task_id,
        'status': task_result.status,
    }
    
    if task_result.status == 'SUCCESS':
        response['result'] = task_result.result
    elif task_result.status == 'FAILURE':
        response['error'] = str(task_result.result)
    
    return jsonify(response)

@app.route('/queryVeritas', methods=['GET'])
def query_veritas():
    """
    GET /queryVeritas
    查询参数: claim=存入数据库的uuid
    
    返回体:
    {
        "status": 200,
        "message": "OK",
        "data": {
            "content": "markdown证据链论证",
            "reference": [
                {
                    "title": "相关链接标题1",
                    "url": "相关链接1",
                    # "relevance": 相关度1,
                    "newstime": "YYYY-MM-DD"
                },
                ...
            ]
        }
    }
    """
    try:
        # 1. 获取并验证请求参数
        claim_uuid = request.args.get('claim')
        if not claim_uuid:
            return jsonify({"status": 400, "message": "Missing claim parameter"}), 400

        # 2. 验证UUID格式
        try:
            UUID(claim_uuid)
        except ValueError:
            return jsonify({"status": 400, "message": "Invalid UUID format"}), 400

        # 3. 获取数据库连接
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 查询验证结果主信息
                cursor.execute("""
                    SELECT 
                        q.title AS original_title,
                        r.content AS evidence_content,
                        r.truth AS verification_result
                    FROM Query q
                    LEFT JOIN Result r ON q.id = r.query_id
                    WHERE q.uuid = %s
                    ORDER BY r.id DESC
                    LIMIT 1
                """, (claim_uuid,))
                result = cursor.fetchone()

                if not result:
                    return jsonify({
                        "status": 404,
                        "message": "Verification record not found"
                    }), 404

                # 查询引用文献
                cursor.execute("""
                    SELECT 
                        title, 
                        url, 
                        newstime
                    FROM Cite
                    WHERE result_id IN (
                        SELECT r.id 
                        FROM Result r
                        JOIN Query q ON r.query_id = q.id
                        WHERE q.uuid = %s
                    )
                """, (claim_uuid,))
                references = cursor.fetchall()
                print(references)
                # 4. 构建Markdown内容
                markdown_content = f"""{result['evidence_content']}
                """.strip()

                # 5. 返回结果
                return Response(
                    json.dumps({
                        "status": 200,
                        "message": "OK", 
                        "data": {
                            "content": markdown_content,
                            "reference": references
                        }
                    }, ensure_ascii=False),  # 关键参数
                    mimetype='application/json; charset=utf-8'
                )
                # return jsonify({
                #     "status": 200,
                #     "message": "OK",
                #     "data": {
                #         "content": markdown_content,
                #         "reference": references
                #     }
                #  })

        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Database query error: {e}")
            return jsonify({
                "status": 500,
                "message": "Database operation failed"
            }), 500
        finally:
            conn.close()

    except Exception as e:
        logger.exception("Unexpected error in queryVeritas")
        return jsonify({
            "status": 500,
            "message": f"Internal server error: {str(e)}"
        }), 500



# ==================== 新增回调相关接口 ====================

@app.route('/setGlobalCallback', methods=['POST'])
def set_global_callback():
    """设置全局回调URL"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": 400, "message": "Empty request body"}), 400
        
        callback_url = data.get('callback_url')

        
        if not callback_url:
            return jsonify({"status": 400, "message": "callback_url is required"}), 400
        
        success = callback_manager.set_global_callback(callback_url)
        
        if success:
            return jsonify({
                "status": 200,
                "message": "Global callback URL set successfully",
                "data": {
                    "callback_url": callback_url
                }
            })
        else:
            return jsonify({"status": 500, "message": "Failed to set global callback"}), 500
    
    except Exception as e:
        logger.exception("Error in setGlobalCallback")
        return jsonify({"status": 500, "message": f"Internal server error: {str(e)}"}), 500


@app.route('/registerCallback', methods=['POST'])
def register_callback():
    """为特定claim注册回调"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": 400, "message": "Empty request body"}), 400
        
        claim_uuid = data.get('claim')
        callback_url = data.get('callback_url')
        
        if not claim_uuid or not callback_url:
            return jsonify({
                "status": 400, 
                "message": "Both claim and callback_url are required"
            }), 400
        
        # 验证UUID格式
        try:
            UUID(claim_uuid)
        except ValueError:
            return jsonify({"status": 400, "message": "Invalid UUID format"}), 400
        
        success = callback_manager.register_callback(claim_uuid, callback_url)
        
        if success:
            return jsonify({
                "status": 200,
                "message": "Callback registered successfully",
                "data": {
                    "claim": claim_uuid,
                    "callback_url": callback_url
                }
            })
        else:
            return jsonify({"status": 500, "message": "Failed to register callback"}), 500
    
    except Exception as e:
        logger.exception("Error in registerCallback")
        return jsonify({"status": 500, "message": f"Internal server error: {str(e)}"}), 500


@app.route('/callbackStatus/<claim_uuid>', methods=['GET'])
def get_callback_status(claim_uuid):
    """查询回调状态"""
    try:
        # 验证UUID格式
        try:
            UUID(claim_uuid)
        except ValueError:
            return jsonify({"status": 400, "message": "Invalid UUID format"}), 400
        
        status_info = callback_manager.get_callback_status(claim_uuid)
        
        return jsonify({
            "status": 200,
            "message": "OK",
            "data": status_info
        })
    
    except Exception as e:
        logger.exception("Error in get_callback_status")
        return jsonify({"status": 500, "message": f"Internal server error: {str(e)}"}), 500


@app.route('/callbackStatistics', methods=['GET'])
def get_callback_statistics():
    """获取回调统计信息"""
    try:
        stats = callback_manager.get_statistics()
        
        return jsonify({
            "status": 200,
            "message": "OK",
            "data": stats
        })
    
    except Exception as e:
        logger.exception("Error in get_callback_statistics")
        return jsonify({"status": 500, "message": f"Internal server error: {str(e)}"}), 500


@app.route('/clearCallback/<claim_uuid>', methods=['POST'])
def clear_callback(claim_uuid):
    """清除特定claim的回调配置"""
    try:
        # 验证UUID格式
        try:
            UUID(claim_uuid)
        except ValueError:
            return jsonify({"status": 400, "message": "Invalid UUID format"}), 400
        
        success = callback_manager.clear_callback(claim_uuid)
        
        if success:
            return jsonify({
                "status": 200,
                "message": "Callback cleared successfully",
                "data": {"claim": claim_uuid}
            })
        else:
            return jsonify({"status": 500, "message": "Failed to clear callback"}), 500
    
    except Exception as e:
        logger.exception("Error in clear_callback")
        return jsonify({"status": 500, "message": f"Internal server error: {str(e)}"}), 500



# ==================== 新增 redoVeritas 接口 ====================

@app.route('/redoVeritas', methods=['POST'])
def redo_veritas():
    """重新验证已有的claim"""
    try:
        # 1. 验证输入
        data = request.get_json()
        if not data:
            return jsonify({"status": 400, "message": "Empty request body"}), 400
        
        claim_uuid = data.get('claim')
        callback_url = data.get('callback_url')  # 可选，覆盖原有回调

        
        if not claim_uuid:
            return jsonify({"status": 400, "message": "claim is required"}), 400
        
        # 2. 验证UUID格式
        try:
            UUID(claim_uuid)
        except ValueError:
            return jsonify({"status": 400, "message": "Invalid UUID format"}), 400
        
        # 3. 从数据库查询原始信息
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 查询原始title和query_id
                cursor.execute("""
                    SELECT q.id as query_id, q.title, q.url
                    FROM Query q
                    WHERE q.uuid = %s
                """, (claim_uuid,))
                query_data = cursor.fetchone()
                
                if not query_data:
                    return jsonify({
                        "status": 404,
                        "message": "Claim not found"
                    }), 404
                
                title = query_data['title']
                query_id = query_data['query_id']
                
        except psycopg2.Error as e:
            logger.error(f"Database query error: {e}")
            return jsonify({"status": 500, "message": "Database operation failed"}), 500
        finally:
            conn.close()
        
        # 4. 创建新的Result记录（用于重新验证）
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Result (title, query_id, status)
                    VALUES (%s, %s, 'pending')
                    RETURNING id
                """, (title, query_id))
                new_result_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Created new Result record for redo: id={new_result_id}")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to create Result record: {e}")
            return jsonify({"status": 500, "message": f"Database error: {str(e)}"}), 500
        finally:
            if conn:
                conn.close()
        
        # 5. 启动新的Celery任务
        task = run_chat_task.apply_async(args=[title, new_result_id])
        logger.info(f"Started redo Celery task {task.id} for claim {claim_uuid}")
        
        # 6. 注册回调
        callback_registered = False
        if callback_url:
            # 使用新的回调URL
            callback_registered = callback_manager.register_callback(
                claim_uuid, callback_url
            )
        else:
            # 检查是否已有回调配置
            existing_callback = callback_manager.get_callback_url(claim_uuid)
            callback_registered = existing_callback is not None
        
        # 7. 返回响应
        response_data = {
            "claim": claim_uuid,
            "new_task_id": task.id,
            "callback_registered": callback_registered,
            "message": "Verification restarted successfully"
        }
        
        if callback_url and callback_registered:
            response_data["callback_url"] = callback_url
        
        return jsonify({
            "status": 200,
            "message": "OK",
            "data": response_data
        })
        
    except Exception as e:
        logger.exception("Unexpected error in redo_veritas")
        return jsonify({"status": 500, "message": f"Internal server error: {str(e)}"}), 500


# ==================== 新增 batchRedoVeritas 接口 ====================

@app.route('/batchRedoVeritas', methods=['POST'])
def batch_redo_veritas():
    """批量重新验证claims"""
    try:
        # 1. 验证输入
        data = request.get_json()
        if not data:
            return jsonify({"status": 400, "message": "Empty request body"}), 400
        
        claims = data.get('claims')
        callback_url = data.get('callback_url')  # 可选的批量回调地址

        
        if not claims or not isinstance(claims, list):
            return jsonify({"status": 400, "message": "claims must be a non-empty list"}), 400
        
        if len(claims) > 100:  # 限制批量大小
            return jsonify({"status": 400, "message": "Too many claims, maximum is 100"}), 400
        
        # 2. 验证UUID格式
        invalid_claims = []
        for claim in claims:
            try:
                UUID(claim)
            except ValueError:
                invalid_claims.append(claim)
        
        if invalid_claims:
            return jsonify({
                "status": 400,
                "message": "Invalid UUID format",
                "data": {"invalid_claims": invalid_claims}
            }), 400
        
        # 3. 处理每个claim
        results = []
        for claim_uuid in claims:
            try:
                # 这里可以优化为批量数据库查询，但为了简单先逐个处理
                # 实际使用时可以根据需要优化
                
                # 创建新的验证任务（简化处理，实际可能需要更多逻辑）
                conn = get_db_connection()
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute("""
                            SELECT q.id as query_id, q.title
                            FROM Query q
                            WHERE q.uuid = %s
                        """, (claim_uuid,))
                        query_data = cursor.fetchone()
                        
                        if query_data:
                            # 创建新的Result记录
                            with conn.cursor() as cursor2:
                                cursor2.execute("""
                                    INSERT INTO Result (title, query_id, status)
                                    VALUES (%s, %s, 'pending')
                                    RETURNING id
                                """, (query_data['title'], query_data['query_id']))
                                new_result_id = cursor2.fetchone()[0]
                                conn.commit()
                                
                                # 启动任务
                                task = run_chat_task.apply_async(
                                    args=[query_data['title'], new_result_id]
                                )
                                
                                # 注册回调
                                if callback_url:
                                    callback_manager.register_callback(
                                        claim_uuid, callback_url
                                    )
                                
                                results.append({
                                    "claim": claim_uuid,
                                    "status": "started",
                                    "task_id": task.id,
                                    "message": "Verification restarted"
                                })
                        else:
                            results.append({
                                "claim": claim_uuid,
                                "status": "failed",
                                "message": "Claim not found"
                            })
                
                except Exception as e:
                    results.append({
                        "claim": claim_uuid,
                        "status": "failed",
                        "message": str(e)
                    })
                finally:
                    if conn:
                        conn.close()
            
            except Exception as e:
                results.append({
                    "claim": claim_uuid,
                    "status": "failed",
                    "message": str(e)
                })
        
        # 4. 统计结果
        started_count = sum(1 for r in results if r['status'] == 'started')
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        
        return jsonify({
            "status": 200,
            "message": f"Batch processing completed: {started_count} started, {failed_count} failed",
            "data": {
                "total": len(claims),
                "started": started_count,
                "failed": failed_count,
                "results": results
            }
        })
        
    except Exception as e:
        logger.exception("Unexpected error in batch_redo_veritas")
        return jsonify({"status": 500, "message": f"Internal server error: {str(e)}"}), 500
    
if __name__ == '__main__':     
    app.run(host='0.0.0.0', port=5000, debug=True)

