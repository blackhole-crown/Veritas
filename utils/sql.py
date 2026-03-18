import os
import sys
import json
import psycopg2
import time
from flask import Flask
from psycopg2 import sql   
import json
import psycopg2
from typing import  Dict, Any, Optional

# 配置部分
# 动态添加项目根目录到 PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)
    
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 这里换到新的环境要重新配置数据库，所以这里也要改，home
app = Flask(__name__)
DB_CONFIG = {
    'dbname': 'veritas_news',
    'user': 'Veritas', 
    'host': '139.224.18.139',
    'port': '5433',
    'password': 'Veritas.'
}

CACHE_PATH = "../.cache/origin_judge.jsonl"
MAX_RETRIES = 3
RETRY_DELAY = 1  # 秒


def get_db_connection():
    """获取数据库连接"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        app.logger.error(f"Database connection failed: {e}")
        raise

def insert_query(title, url, source):
    """插入Query表并返回UUID，添加重试机制"""
    for attempt in range(MAX_RETRIES):
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    sql.SQL("""
                        INSERT INTO Query (title, url, source) 
                        VALUES (%s, %s, %s) 
                        RETURNING uuid, id
                    """), (title, url, source))
                result = cursor.fetchone()
                conn.commit()
                return {'uuid': result[0], 'id': result[1]}
        except psycopg2.InterfaceError as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY)   #炸弹
            continue
        except psycopg2.DatabaseError as e:
            conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
   


def get_result_from_cache(title):
    """更健壮的缓存读取实现 - 修复版本"""
    try:
        if not os.path.exists(CACHE_PATH):
            return None
            
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if item.get("description") == title:
                        history = item.get("history", {})
                        
                        # 修复：按优先级顺序检查k值
                        k_priority = ['k=5', 'k=10', 'k=15', 'k=20']
                        
                        for k in k_priority:
                            records = history.get(k, [])
                            if records:  # 如果该k值有记录
                                last_result = records[-1].get("Result", "").upper()
                                if last_result == "TRUE":
                                    return True
                                elif last_result == "FALSE":
                                    return False
                                # 如果Result不是TRUE或FALSE，继续检查下一个k值
                        
                        # 所有k值都没有有效结果
                        return None
                        
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        app.logger.error(f"Error reading cache: {e}")
    return None

def insert_result( 
    result_id: int,
    claim: str,
    jsonl_file_path: str = '.cache/new.jsonl'
 ) -> Dict[str, Any]:
    """更新 Result 记录的内容"""
    truth = False
    content = None
    # 1. 查找 JSONL 中的记录
    try:
        with open(jsonl_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    description = record.get('description', "")
                    if description == claim:
                        history_k5 = record.get('history', {}).get('k=5', [{}])
                        truth = history_k5[0].get('Result') == 'TRUE' if history_k5 else False
                        content = record.get('last_output', {}).get('k=5', '')
                        
                        break
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error: {line[:100]}... Error: {e}")
                    continue
            
        if content is None:
            return {'status': 'error', 'message': '未找到匹配的 claim 记录'}
    except FileNotFoundError:
        return {'status': 'error', 'message': f'JSONL 文件未找到: {jsonl_file_path}'}
    except Exception as e:
        return {'status': 'error', 'message': f'JSONL 处理失败: {str(e)}'}
 
    # 2. 更新数据库
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE Result SET truth = %s, content = %s WHERE id = %s RETURNING id',
                (truth, content, result_id)
            )
            updated_record = cursor.fetchone()
            if not updated_record:
                return {'status': 'error', 'message': '未找到指定的 Result 记录'}
            conn.commit()
            return {'status': 'success', 'action': 'updated', 'result_id': updated_record[0]}
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        return {'status': 'error', 'message': f'数据库错误: {str(e)}'}
    finally:
        if conn:
            conn.close()
  


def insert_cite_references(result_id: int,claim: str, json_file_path: str = ".cache/brave/related_news.jsonl"):
    """
    插入引用数据到 Cite 表（支持 JSONL 文件格式）

    参数:
        claim (str): 要匹配的声明内容
        result_id (int): Cite表的外键 result_id
        json_file_path (str): 包含引用数据的 JSONL 文件路径

    返回:
        dict: 包含操作状态，如:
              {'status': 'success', 'inserted_count': 2}
              或 {'status': 'error', 'message': '错误信息'}
    """

    # 1. 从 JSONL 文件中查找匹配的 claim 数据
    references = []
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                file_claim = data.get('claim')
                if file_claim == claim:
                    references = data.get('collection', [])
                    print(references)
                    break
            else:
                return {'status': 'error', 'message': '未找到匹配的 claim 记录'}
            
    except Exception as e:
        return {'status': 'error', 'message': f'读取 JSONL 文件失败: {str(e)}'}

    # 2. 检查是否有 reference 数据
    if not references:
        return {'status': 'error', 'message': '未找到引用数据'}
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            insert_data = []
            for ref in references:
                title = ref.get('title', '')
                url = ref.get('url')  # 现在可以为None
                date_str = ref.get('date', '')
                # relevance_str = ref.get('relevance', '')
                
                # # 处理relevance
                # relevance = None
                # if relevance_str and relevance_str.lower() != 'none':
                #     try:
                #         relevance = 95
                #     except ValueError:
                #         pass
                
                insert_data.append((title, url, date_str, result_id))    #, relevance

            if not insert_data:
                return {'status': 'warning', 'message': '没有有效数据可插入'}
            
            print(insert_data)
            
            cursor.executemany(
                """
                INSERT INTO Cite (
                    title,
                    url,
                    newstime,
                    result_id
                ) VALUES (
                    %s, %s, %s, %s
                )
                """,
                insert_data
            )

            conn.commit()
            return {
                'status': 'success',
                'inserted_count': len(insert_data),
                'total_references': len(references)
            }

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        return {'status': 'error', 'message': f'数据库错误: {str(e)}'}
    finally:
        if conn:
            conn.close()