# -*- coding: utf-8 -*-
import sys
import json
from typing import Dict, Union
dirs = ["../swift2/my_inferencing"] 
for _dir in dirs:
    if _dir not in sys.path:
        sys.path.append(_dir)
from . import utils
# 在文件开头添加
import logging

# 禁用pydoll的INFO级别日志
logging.getLogger("pydoll").setLevel(logging.WARNING)
logging.getLogger("pydoll.connection").setLevel(logging.WARNING)
logging.getLogger("pydoll.browser").setLevel(logging.WARNING)
# import add_date
from datetime import datetime
import os, time
import re
import requests
import http.client
http.client.HTTPConnection._http_vsn = 10
http.client.HTTPConnection._http_vsn_str = 'HTTP/1.0'

from requests.adapters import HTTPAdapter
s = requests.Session()




# 导入同花顺爬虫模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from ths_crawler import get_ths_search_result
    from brave_crawler import crawl_news
except ImportError as e:
    print(f"导入ths_crawler_v2失败: {e}")
    # 如果导入失败，尝试相对导入
    try:
        from .ths_crawler import get_ths_search_result
        from .brave_crawler import crawl_news
    except ImportError:
        print("无法导入同花顺爬虫模块")
        get_ths_search_result = None


max_retries = 10
s.mount('http://', HTTPAdapter(max_retries=max_retries))
s.mount('https://', HTTPAdapter(max_retries=max_retries))

search_engine = "ths"  # 目前只支持：ths，brave


def remove_quotation_marks(claim: str):
    """删除双引号"""
    return claim.strip().replace("“", "").replace("”", "").replace("\"", "").replace("NOT", "not")

def __get_web_result(query, count=10):
    """
    根据当前选择的搜索引擎获取网页结果
    """
    if search_engine == "ths":
        return __get_web_result_ths(query, count)
    elif search_engine == "brave":
        return __get_web_result_brave(query, count)
    else:
        print(f"错误：未知的搜索引擎 {search_engine}")
        # 返回空结果
        return {
            'type': 'search',
            'query': {'original': query, 'more_results_available': False},
            'web': {'results': []}
        }

def __get_web_result_ths(query, count=10):
    """
    使用同花顺爬虫获取网页结果（替换原来的Brave API调用）
    """
    # 检查爬虫模块是否可用
    if get_ths_search_result is None:
        print("错误：同花顺爬虫模块不可用")
        # 返回空的Brave API格式结果
        return {
            'type': 'search',
            'query': {
                'original': query,
                'show_strict_warning': False,
                'is_navigational': False,
                'is_news_breaking': False,
                'spellcheck_off': False,
                'country': 'cn',
                'bad_results': False,
                'should_fallback': False,
                'postal_code': '',
                'city': '',
                'header_country': '',
                'more_results_available': False,
                'state': ''
            },
            'web': {
                'type': 'search',
                'results': [],
                'family_friendly': True
            }
        }
    
    try:
        # print(f"使用同花顺爬虫搜索: {query}，数量: {count}")
        # 注意这里要传递count参数
        result = get_ths_search_result(query, count)
        # print(f"爬虫返回 {len(result.get('web', {}).get('results', []))} 个结果")
        return result
    except Exception as e:
        print(f"同花顺爬虫执行出错: {e}")
        import traceback
        print(traceback.format_exc())
        # 返回空结果
        return {
            'type': 'search',
            'query': {'original': query, 'more_results_available': False},
            'web': {'results': []}
        }



def __get_web_result_brave(query, count=10):
    """
    使用Brave搜索爬虫获取网页结果（替换原来的同花顺爬虫）
    """
    try:
        # 使用异步方式运行crawl_news
        import asyncio
        
        # 创建新的事件循环或获取当前事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 运行爬虫，获取结果
        brave_results = loop.run_until_complete(crawl_news(query, count))
        
        # 将Brave搜索结果转换为原有格式
        formatted_results = []
        for item in brave_results:
            formatted_results.append({
                'title': item['title'],
                'url': item['url'],
                'description': item['description'],
                'date': item['parsed_date'],
                'author': item['author'],
                'source': item['source']
            })
        
        # 构建与原来同花顺爬虫相同格式的返回结果
        return {
            'type': 'search',
            'query': {
                'original': query,
                'show_strict_warning': False,
                'is_navigational': False,
                'is_news_breaking': False,
                'spellcheck_off': False,
                'country': 'cn',
                'bad_results': False,
                'should_fallback': False,
                'postal_code': '',
                'city': '',
                'header_country': '',
                'more_results_available': len(formatted_results) >= count,
                'state': ''
            },
            'web': {
                'type': 'search',
                'results': formatted_results,
                'family_friendly': True
            }
        }
        
    except Exception as e:
        print(f"Brave搜索爬虫执行出错: {e}")
        import traceback
        print(traceback.format_exc())
        # 返回空结果
        return {
            'type': 'search',
            'query': {'original': query, 'more_results_available': False},
            'web': {'results': []}
        }




def get_brave_search(news, query_date, K):
    """
    返回：search_res, news_id, last_output
    """
    assert utils.DATE_THRESHOLD >= 1, 'DATE_THRESHOLD neads to >= 1'
    news = news.strip()
    news_item = utils.get_news_item(news)
    query_history = news_item["history"][f"k={K}"]
    
    add_news_to_jsonl(news_item,news)    # 这个是加入claim到jsonl文件
    
    if len(query_history) == 0:
        search_res = __get_web_result(remove_quotation_marks(news))
        utils.add_search(
            {"id": news_item["id"], f"{search_engine}_search_results": search_res})

        return search_res, news_item["id"], None
    else:
        if utils.is_within_days(
            query_date, query_history[-1]["Date"], utils.DATE_THRESHOLD):

            return None, news_item["id"], news_item["last_output"][f"k={K}"]
        else:
            search_res = __get_web_result(remove_quotation_marks(news))
            utils.update_search(news_item["id"], search_engine, search_res)
            return search_res, news_item["id"], None



def add_news_to_jsonl(news_item, news, file_path: str = ".cache/brave/related_news.jsonl"):
    """
    将新闻条目添加到JSONL文件
    
    参数:
    news_item (dict): 包含新闻数据的字典，必须有"id"键
    news (str): 新闻内容
    file_path (str): JSONL文件的路径
    
    返回:
    bool: 添加成功返回True，失败返回False
    """

    
    try:
        # 确保新闻条目包含必要的键和内容
        if "id" not in news_item:
            raise ValueError("新闻条目必须包含'id'键")
        if news is None:
            raise ValueError("新闻内容不能为None")
        
        # 创建要添加的条目
        entry = {
            "id": news_item["id"],
            "claim": news
        }
        
        # 检查文件是否存在并获取已有ID
        existing_ids = set()
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        existing_entry = json.loads(line)
                        if "id" in existing_entry:  # 只处理包含id字段的条目
                            existing_ids.add(existing_entry["id"])
                    except json.JSONDecodeError:
                        continue  # 跳过无效行
            
            # 检查新ID是否重复
            if entry["id"] in existing_ids:
                print(f"警告: ID {entry['id']} 已存在，跳过添加")
                return False
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 以追加模式写入新条目
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"成功添加ID为 {entry['id']} 的新闻条目")
        
        # ========== 新增：创建基础的result.jsonl条目（只有id、description和revelent_news的基本信息）==========
        result_file_path = ".cache/result.jsonl"
        
        # 创建基础的result.jsonl条目
        base_result_entry = {
            "id": entry["id"],
            "description": news,  # description使用claim
            "history": {
                "k=5": [],
                "k=10": [],
                "k=15": [],
                "k=20": []
            },
            "last_output": {
                "k=5": "",
                "k=10": "",
                "k=15": "",
                "k=20": ""
            },
            "revelent_news": {
                "id": entry["id"],
                "claim": news,
                "collection": []  # 初始为空，后续由write_records_to_jsonl填充
            }
        }
        
        # 检查result.jsonl是否存在
        result_records = []
        if os.path.exists(result_file_path):
            with open(result_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        result_records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        # 确保result目录存在
        os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
        
        # 如果ID不存在，则添加基础记录
        id_exists = False
        for record in result_records:
            if record.get("id") == entry["id"]:
                id_exists = True
                break
        
        if not id_exists:
            with open(result_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(base_result_entry, ensure_ascii=False) + '\n')

        
        return True
        # ========== 新增结束 ==========
    
    except Exception as e:
        print(f"添加新闻条目时出错: {e}")
        return False