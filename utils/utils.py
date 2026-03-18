import json
import datetime
import os
import pandas as pd
import requests
import re

NEWS_DIR = '.cache/new.jsonl'
NEWS_SEARCH_DIR = '.cache/brave/new_search.json'


DEFUALT_K = 5
DATE_THRESHOLD = 1 
split_contexts = True

EMPTY_DF = pd.DataFrame([{"": ""}])



import tempfile
import shutil

def dump_jsonl(data, file_dir):
    """安全写入JSONL文件，使用原子操作"""
    # 确保目录存在
    os.makedirs(os.path.dirname(file_dir), exist_ok=True)
    
    # 创建临时文件（修复：简化前缀，避免文件名过长）
    temp_fd, temp_path = tempfile.mkstemp(
        dir=os.path.dirname(file_dir) or '.',
        suffix='.tmp'
    )
    
    try:
        # 写入临时文件
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            for item in data:
                try:
                    # 验证数据是可序列化的字典
                    if isinstance(item, dict):
                        json.dump(item, f, ensure_ascii=False)
                        f.write('\n')
                    else:
                        print(f"Warning: Skipping non-dict item: {type(item)}")
                except (TypeError, ValueError) as e:
                    print(f"Warning: Skipping item that cannot be serialized: {e}")
                    continue
        
        # 原子替换：重命名临时文件为目标文件
        shutil.move(temp_path, file_dir)
        
    except Exception as e:
        # 清理临时文件
        try:
            os.unlink(temp_path)
        except:
            pass
        print(f"Error writing to {file_dir}: {e}")
        raise


def load_jsonl(file_dir):
    data = []
    if not os.path.exists(file_dir):
        return data
    
    try:
        with open(file_dir, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    # 基本数据验证
                    if isinstance(item, dict):
                        data.append(item)
                    else:
                        print(f"Warning: Line {line_num} is not a JSON object, skipping")
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error at line {line_num}: {e}")
                    print(f"  Line content: {line[:100]}...")
                    continue
    except Exception as e:
        print(f"Error reading file {file_dir}: {e}")
    
    return data

def get_all_news():
    return load_jsonl(NEWS_DIR)


# utils/utils.py

def get_all_news_search():
    """
    获取所有的新闻搜索记录
    Returns:
        list: 新闻搜索记录的列表
    """
    try:
        # 确保文件存在
        if not os.path.exists(NEWS_SEARCH_DIR):
            # 如果文件不存在，创建一个空的列表
            with open(NEWS_SEARCH_DIR, 'w', encoding='utf-8') as file:
                json.dump([], file, ensure_ascii=False, indent=2)
            return []
        
        # 检查文件是否为空
        if os.path.getsize(NEWS_SEARCH_DIR) == 0:
            return []
        
        with open(NEWS_SEARCH_DIR, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:  # 如果文件内容为空
                return []
            
            # 尝试解析JSON
            data = json.loads(content)
            # 确保返回的是列表
            return data if isinstance(data, list) else []
            
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print("文件内容:", content if 'content' in locals() else "无法读取内容")
        # 备份损坏的文件
        if os.path.exists(NEWS_SEARCH_DIR):
            backup_file = NEWS_SEARCH_DIR + ".backup_" + time.strftime("%Y%m%d_%H%M%S")
            shutil.copy2(NEWS_SEARCH_DIR, backup_file)
            print(f"已备份损坏的文件到: {backup_file}")
        
        # 创建新的空文件
        with open(NEWS_SEARCH_DIR, 'w', encoding='utf-8') as file:
            json.dump([], file, ensure_ascii=False, indent=2)
        return []
    except Exception as e:
        print(f"读取新闻搜索记录时出错: {e}")
        return []

def get_today():
    return datetime.datetime.today().strftime("%Y-%m-%d")

def get_news_item(news) -> dict:
    """
    获取news id，如果没有这条news，那么会添加到news列表

    返回 news_id, last_query_date
    """
    def get_new_id(news, news_list):
        # 首先检查是否已存在相同的新闻
        for item in news_list:
            if item["description"] == news:
                return item["id"], item
        
        # 如果不存在，找到最大的ID并加1
        max_id = 0
        for item in news_list:
            if item["id"] > max_id:
                max_id = item["id"]
        
        return max_id + 1, None

    
    news = news.strip()
    news_list = get_all_news()
    new_id, news_item = get_new_id(news, news_list)

    if news_item is not None:
        return news_item
    
    news_item = {
        "id": new_id, 
        'description': news, 
        "history": {"k=5": [], "k=10": [], "k=15": [], "k=20": []}, 
        "last_output": {"k=5": "", "k=10": "", "k=15": "", "k=20": ""}
    }
    news_list.append(news_item)
    news_list.sort(key=lambda x: x['id'])

    # 写入JSONL文件
    dump_jsonl(news_list, NEWS_DIR)
    return news_item

def update_query_history(news_id, query_date, res_coe, K, update=True):
    def get_classify_result(res_coe):
        res_filtered = res_coe[res_coe.rfind("**Final Judgment**"):]
        if "TRUE" in res_filtered:
            return "TRUE"
        elif "FALSE" in res_filtered:
            return "FALSE"
        else:
            print("Error result!!!")

    news_list = get_all_news()
    result = get_classify_result(res_coe)
    query_history = None
    for item in news_list:
        if item["id"] == news_id:
            if update:
                item["history"][f"k={K}"].append({"Date": query_date, "Result": result})
                item["last_output"][f"k={K}"] = res_coe
            query_history = item["history"]
            break
    
    if update:
        dump_jsonl(news_list, NEWS_DIR)
    return query_history

def add_search(search_item):

    news_search = get_all_news_search()

    news_search.append(search_item)
    news_search.sort(key=lambda x: x['id'])

    with open(NEWS_SEARCH_DIR, 'w') as file:
        json.dump(news_search, file, indent=4)

def update_search(news_id , search_engine, search_res):
    news_search = get_all_news_search()

    for item in news_search:
        if item["id"] == news_id:
            item[f"{search_engine}_search_results"] = search_res
            break

    with open(NEWS_SEARCH_DIR, 'w') as file:
        json.dump(news_search, file, indent=4)


def is_within_days(query_date: str, last_date: str, n: int) -> bool:
    """
    检查date2是否比date1早n天以内
    
    Args:
        date1: 第一个日期，格式为"YYYY-MM-DD"
        date2: 第二个日期，格式为"YYYY-MM-DD"
        n: 天数阈值
        
    Returns:
        bool: 如果date2比date1早n天以内返回True，否则返回False
    """
    from datetime import datetime
    
    # 将字符串转换为datetime对象
    d1 = datetime.strptime(query_date, "%Y-%m-%d")
    d2 = datetime.strptime(last_date, "%Y-%m-%d")
    
    # 计算日期差
    diff = d1 - d2
    
    # 检查日期差是否在n天以内且date2比date1早
    return 0 <= diff.days < n

def delete_txt_files(directory_path):
    """Delete all .txt files in specified directory
        清理input文件？
    """
    if not os.path.exists(directory_path):
        raise ValueError(f"Directory does not exist: {directory_path}")
        
    for filename in os.listdir(directory_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory_path, filename)
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")




def origin_judge(news, query_data, k):


    # 1. 参数验证
    if not isinstance(news, str) or not news.strip():
        print("Warning: Invalid news input")
        return "ERROR"
    
    if not isinstance(query_data, dict):
        print("Warning: query_data should be a dictionary")
        return "ERROR"
    # 这里改成实际部署的模型和端口
    # 1. 调用模型API判断新闻真实性
    # 改了这里记得改settings.yaml
    url = "http://127.0.0.1:8006/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "Qwen3-4B-Instruct-2507",
        "messages": [
           {
               "role": "system",
              "content": """你是一个新闻真实性判断专家，只能输出TRUE或FALSE。
              判断原则：
             1. 对于无法确认的新闻，一律输出FALSE
             2. 重点关注逻辑矛盾和常识错误
             3. 警惕转折句（如"但是"、"然而"）后的信息
             4. 不依赖外部知识，仅基于新闻本身的内在逻辑

             示例：
             新闻："某国科学家发现永动机" -> FALSE (违反物理常识)
             新闻："虽然有人说地球是平的，但科学研究证明地球是圆的" -> TRUE (转折后是正确信息)
             新闻："某公司宣称开发出治疗所有癌症的药物" -> FALSE (过于绝对的宣称)"""
           },
         {
            "role": "user",
            "content": f"新闻内容：{news}\n\n请判断该新闻是否真实（无法确认请输出FALSE）："
        }
    ],
    "max_tokens": 5,
    "temperature": 0,
}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        judgment = result["choices"][0]["message"]["content"]
        
        # 验证API返回结果
        if judgment not in ["TRUE", "FALSE"]:
            print(f"Warning: Unexpected API response: {judgment}")
            judgment = "ERROR"
            
    except requests.exceptions.Timeout:
        print("API调用超时")
        judgment = "ERROR"
    except requests.exceptions.RequestException as e:
        print(f"API调用失败: {e}")
        judgment = "ERROR"
    except (KeyError, ValueError) as e:
        print(f"API响应解析失败: {e}")
        judgment = "ERROR"
    
    # 2. 准备要存储的数据
    entry = {
        "Date": query_data,
        "Result": judgment
    }
    
    # 3. 读取或创建JSONL文件
    file_path = ".cache/origin_judge.jsonl" 
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 使用统一的load_jsonl函数读取数据
    existing_data = load_jsonl(file_path)

    max_id = 0
    found = False
    
    # 计算最大ID并查找现有条目
    for item in existing_data:
        # 验证item结构
        if not isinstance(item, dict):
            continue
            
        # 获取最大ID（修复：正确处理id字段）
        if 'id' in item:
            try:
                item_id = int(item['id'])  # 确保id是整数
                max_id = max(max_id, item_id)
            except (ValueError, TypeError):
                # 如果id不是有效数字，跳过这个item
                continue
        
        # 查找匹配的新闻
        if item.get("description") == news:
            found = True
            key = f"k={k}"
            
            # 确保history存在
            if 'history' not in item or not isinstance(item['history'], dict):
                item['history'] = {}
            
            # 确保key存在
            if key not in item['history']:
                item['history'][key] = []
            
            # 添加新记录
            item['history'][key].append(entry)
            break
    
    if not found:
        # 创建新条目，使用最大ID+1作为新ID
        new_entry = {
            "id": max_id + 1,
            "description": news,
            "history": {
                f"k={k}": [entry],
                "k=10": [],
                "k=15": [],
                "k=20": []
            }
        }
        existing_data.append(new_entry)
    
    # 5. 写回文件
    try:
        dump_jsonl(existing_data, file_path)
    except Exception as e:
        print(f"Failed to write data to file: {e}")
    
    return judgment


def merge_to_result_jsonl(news_id, message):
    """
    将new.jsonl和related_news.jsonl中的数据合并到result.jsonl
    
    参数:
        news_id: 新闻ID
        message: 原始新闻内容（作为备用的description和claim）
    
    返回:
        bool: 合并成功返回True，失败返回False
    """
    try:
        # 1. 从 new.jsonl 读取完整的新闻数据（包括 history 和 last_output）
        new_jsonl_path = ".cache/new.jsonl"
        new_record_data = None
        if os.path.exists(new_jsonl_path):
            with open(new_jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("id") == news_id:
                            new_record_data = record
                            break
                    except json.JSONDecodeError:
                        continue
        
        if not new_record_data:
            print(f"警告: 在new.jsonl中未找到ID为 {news_id} 的记录")
            return False
        
        # 2. 从 related_news.jsonl 读取 collection 数据
        related_news_path = ".cache/brave/related_news.jsonl"
        related_record_data = None
        if os.path.exists(related_news_path):
            with open(related_news_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("id") == news_id:
                            related_record_data = record
                            break
                    except json.JSONDecodeError:
                        continue
        
        if not related_record_data:
            print(f"警告: 在related_news.jsonl中未找到ID为 {news_id} 的记录")
            return False
        
        # 3. 构建完整的 result.jsonl 条目
        complete_result_entry = {
            "id": news_id,
            "description": new_record_data.get("description", message),
            "history": new_record_data.get("history", {
                "k=5": [], "k=10": [], "k=15": [], "k=20": []
            }),
            "last_output": new_record_data.get("last_output", {
                "k=5": "", "k=10": "", "k=15": "", "k=20": ""
            }),
            "revelent_news": {
                "id": news_id,
                "claim": related_record_data.get("claim", message),
                "collection": related_record_data.get("collection", [])
            }
        }
        
        # 4. 读取现有的 result.jsonl
        result_path = ".cache/result.jsonl"
        result_records = []
        if os.path.exists(result_path):
            with open(result_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        result_records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        # 5. 更新或添加记录
        result_updated = False
        for i, record in enumerate(result_records):
            if record.get("id") == news_id:
                result_records[i] = complete_result_entry
                result_updated = True
                break
        
        if not result_updated:
            result_records.append(complete_result_entry)
        
        # 6. 写入 result.jsonl
        os.makedirs(os.path.dirname(result_path), exist_ok=True)
        with open(result_path, 'w', encoding='utf-8') as f:
            for record in result_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        return True
        
    except Exception as e:
        print(f"合并数据到result.jsonl时出错: {e}")
        import traceback
        traceback.print_exc()
        return False