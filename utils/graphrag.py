import os
import shutil
import subprocess
import sys
import pandas as pd
import re
import json
from typing import List, Dict, Optional
from . import utils
import datatime

dirs = [
    "swift2/my_inferencing/create_prompt_llm", 
    "swift2/my_inferencing"]  
for _dir in dirs:
    if _dir not in sys.path:
        sys.path.append(_dir)

import prompt_rag

class DataTableKey:
    entities = "Entities"
    relationships = "Relationships"
    documents = "Documents"
    text_units = "Text Units"
    communities = "Communities"
    community_reports = "Community Reports"
    # covariates = "Covariates"
    
query_methond = 'local'  # 这里是选择graph的查询方法  local / global
root_dir = f'graphrag/sample' 
def get_outputs_dir(K):
    outputs_dir = f'./.cache/graphrag/outputs_k={K}'
    return outputs_dir
contexts_dir = os.path.join(root_dir, 'input', 'contexts.txt')
output_dir = os.path.join(root_dir, 'output')

def init_graph():
    """
    这就是删除output文件的函数
    """
    cache_dir = os.path.join(root_dir, 'cache')
    logs_dir = os.path.join(root_dir, 'logs')
    input_dir = os.path.join(root_dir, 'input')

    utils.delete_txt_files(input_dir)

    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)

    if os.path.exists(logs_dir):
        shutil.rmtree(logs_dir)

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

def try_load_output(news_id, K, last_output):
    if os.path.exists(get_outputs_dir(K) + f'/output_{news_id}') and last_output is not None:
        shutil.copytree(get_outputs_dir(K) + f'/output_{news_id}', root_dir + '/output')
        return True
    else:
        return False

def build_graph(search_res, news_id, K, last_output, split_contexts):           #search_res: 搜索结果（列表） news_id: 当前处理新闻的唯一标识符。K: 从搜索结果中提取的上下文数量。last_output: 上一次的输出结果，判断是否需要重新构建图。split_contexts: 布尔值，指示是否将上下文拆分为多个部分
    
    init_graph()
    all_records = [] # 记录每次搜索结果
    if last_output is None:
        
        
        snippet = prompt_rag.get_brave_snippet(
            search_res, ids=slice(0, K),
            ret_type = 'list' if split_contexts else 'str',
            # max_len=100
        )

        # 导入contexts,这里是把爬起到的相关新闻放到input文件夹的代码
        # 可以直接在这里修改，把相关新闻插入到那个relevant_news里面，再通过那边写入数据库
        # 现在问题是需要把爬取到的新闻的url也存储
        # 这里把爬取的列表的信息写入文件，我直接在这里把这些信息写到related_news里面
        if isinstance(snippet, list):
            snippet = [re.sub(r"^Information \d+:","", context, count=1).strip() for context in snippet]
            url = "\n"+"url:"+""
            title = ""
            for i, context in enumerate(snippet):
                try:
        # 提取标题内容
                    url ="url:"+ "\n" + search_res["web"]["results"][i]["url"]
                    url = re.sub(r'^url:', '', url).strip()
                    url = "\n" + url
                    title_match = re.search(r"Title: (.*)", context)
                    if title_match:
                    # 动态创建title_{i}变量并赋值
                        title = title_match.group(1)
                    # 打印提取的标题            
                except (IndexError, KeyError):
                    pass
                
                record = {'id':i+1,'title': title, 'url': url.replace("\n", "")}
                all_records.append(record)
                
                with open(os.path.join(
                    root_dir, 'input', f'context_{i+1}.txt'), 'w', encoding='utf-8') as file:
                    file.write(context + url)
        else:
            with open(contexts_dir, 'w', encoding='utf-8') as file:
                file.write(snippet)

        write_records_to_jsonl(all_records,news_id)
        

    if not try_load_output(news_id, K, last_output):
        subprocess.run([
            'graphrag', 'index', 
            '--root', root_dir], capture_output=True, text=True)
    
    return get_data_table()


    

def get_data_table():               
    data_table = {}                
    # 初始化一个空字典 data_table                                   
    # 加载 graphrag/sample/output/xx.parquet 文件，删除 id 列，并存储到 data_table 中，键为 DataTableKey.xx
    # 这里需要修改，因为文件变了
    
    
    data_table[DataTableKey.community_reports] = pd.read_parquet(
        os.path.join(output_dir, 'community_reports.parquet')).drop(columns=["id"])
    data_table[DataTableKey.entities] = pd.read_parquet(
        os.path.join(output_dir, 'entities.parquet')).drop(columns=["id"])
    data_table[DataTableKey.relationships] = pd.read_parquet(
        os.path.join(output_dir, 'relationships.parquet')).drop(columns=["id"])
    data_table[DataTableKey.documents] = pd.read_parquet(
        os.path.join(output_dir, 'documents.parquet')).drop(columns=["id"])
    data_table[DataTableKey.text_units] = pd.read_parquet(
        os.path.join(output_dir, 'text_units.parquet')).drop(columns=["id"])
    # try:
    #     data_table[DataTableKey.community_reports] = pd.read_parquet("community_reports.parquet")
    # except FileNotFoundError:
    #     logger.warning("社区报告文件未找到，使用空 DataFrame 替代")
    data_table[DataTableKey.community_reports] = pd.DataFrame()  # 默认值
    data_table[DataTableKey.communities] = pd.read_parquet(
            os.path.join(output_dir, 'communities.parquet')).drop(columns=["id"])


    
    ## data_table[DataTableKey.covariates] = pd.read_parquet(
    ##     os.path.join(output_dir, 'create_final_covariates.parquet'))
    # 初始化一个空字典 data_table。
    # 从指定的输出目录（output_dir）加载多个 Parquet 文件，分别对应不同类型的数据表。
    # 对每个加载的数据表，删除 id 列。
    # 将加载后的数据表存储到字典中，以 DataTableKey 的枚举值作为键
    return data_table

def get_data_table_init():          #初始化一个数据表字典
    data_table = {
        DataTableKey.community_reports: pd.DataFrame(),     # community_reports: 社区报告相关的数据表
        DataTableKey.entities: pd.DataFrame(),              # entities: 识别的实体数据表。
        DataTableKey.relationships: pd.DataFrame(),         # relationships: 实体之间关系的数据表。
        DataTableKey.documents: pd.DataFrame(),             # documents: 文档相关的数据表。
        DataTableKey.text_units: pd.DataFrame(),            # text_units: 文本单元（如段落、句子等）相关的数据表。
        DataTableKey.communities: pd.DataFrame(),           # communities: 社区相关的数据表。
    }
    # 键 是 DataTableKey 类中的各种枚举值或常量
    # 值 是每个键对应的空 pandas.DataFrame()，表示初始化时这些数据表为空
    return data_table

def save_graph(_id, K):

    if os.path.exists(get_outputs_dir(K) + f'/output_{_id}'):
        shutil.rmtree(get_outputs_dir(K) + f'/output_{_id}')

    os.rename(output_dir, output_dir + f'_{_id}')
    shutil.move(output_dir + f'_{_id}', get_outputs_dir(K))

def get_answer(output_raw, query_methond):
    #     output_raw: 外部命令的原始输出（字符串格式），可能包含所需答案的文本。
    #     query_methond: 查询方法，决定如何解析 output_raw，支持不同的解析逻辑（例如 "local" 或 "global"）
    if query_methond == "local":
        return output_raw[output_raw.find('Local Search Response:') + len('Local Search Response:'):].strip()
    elif query_methond == "global":
        return output_raw[output_raw.find('Global Search Response:') + len('Global Search Response:'):].strip()
    else:
        raise Exception("Error search method!")

def get_query_coe(news):
#     Q = f"Now you should classify the following NEWS. Please provide a **chain of evidence** as above and give a clear judgment result (TRUE or FALSE, wrapped in **).\n\
# NEWS: **{news}**"

    current_time = datetime.datetime.now().strftime("%Y-%m-%d")
    Q = f"Publication date:{current_time}.You are now required to classify the following NEWS. Please present a **chain of evidence** as outlined above, and provide a definitive judgment result (TRUE or FALSE, wrapped in **).\n\
NEWS: **{news}**"
    
    return Q

def get_COE(news, news_id, K, last_output):
    if last_output is not None:
        return last_output    
    # news: 当前新闻或用户输入的查询内容。
    # news_id: 与当前新闻或查询相关的唯一标识符。
    # K: 可能表示搜索的上下文数量或其他限制条件。
    # last_output: 上一次生成的输出，若存在则直接使用，避免重复计算。
    else:
        result = subprocess.run([            # 使用 subprocess.run 执行外部命令，用于查询或构建证据链
            'graphrag', 'query',             # 'graphrag', 'query': 执行 graphrag 工具中的 query 命令。
            '--root', root_dir,              # '--root', root_dir: 指定根目录 root_dir，可能是存储图数据的位置。
            '--method', query_methond,       # '--method', query_methond: 指定查询方法，变量 query_methond 定义了具体的查询策略。
            '--query', get_query_coe(news)], # '--query', get_query_coe(news): 使用 get_query_coe(news) 函数生成查询字符串。
            capture_output=True, text=True)  # 结果存储在 result 变量中
        
        save_graph(news_id, K)                              #调用 save_graph 函数，保存与新闻 ID 和上下文限制 K 相关的图数据
        
        return get_answer(result.stdout, query_methond)     #调用 get_answer 函数，解析 result.stdout（即外部命令的标准输出）并生成最终的证据链答案
    

def parse_context_file(file_path: str) -> Dict[str, str]:
    """解析context.txt文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    title = ""
    url = ""
    date = "None"
    content_text = ""
    
    lines = content.split('\n')
    for line in lines:
        if line.startswith("Publication date:"):
            date = line.replace("Publication date:", "").strip()
        elif line.startswith("Title:"):
            title = line.replace("Title:", "").strip()
        elif line.startswith("Content:"):
            content_text = line.replace("Content:", "").strip()
        elif line.startswith("url:"):
            url = line.replace("url:", "").strip()
        elif line.strip() and not content_text:
            content_text = line.strip()
    
    return {
        'title': title,
        'url': url,
        'date': date,
        'content': content_text
    }

def read_jsonl_file(file_path: str) -> List[Dict]:
    """读取JSONL文件内容"""
    if not os.path.exists(file_path):
        return []
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    return data

def find_matching_entry(data: List[Dict], claim: str):
    """
    查找匹配的claim条目并返回最大ID
    
    返回:
        (匹配的条目, 最大ID)
    """
    max_id = 0
    for entry in data:
        max_id = max(max_id, entry.get('id', 0))
        if entry.get('claim') == claim:
            return entry, max_id
    return None, max_id

def write_records_to_jsonl(all_records, news_id, output_path=".cache/brave/related_news.jsonl"):
    """
    将all_records写入JSONL文件，与指定的news_id关联
    
    参数:
        all_records: 包含所有记录的列表
        news_id: 要关联的新闻ID
        output_path: JSONL文件输出路径
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 读取现有JSONL文件（如果存在）
    records = []
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    # 查找是否存在对应news_id的记录
    existing_record = None
    for record in records:
        if record.get("id") == news_id:
            existing_record = record
            break
    
    # 构建要写入的新记录（保留原有claim字段）
    if existing_record:
        # 存在旧记录，仅更新collection字段，保留其他字段（包括claim）
        existing_record["collection"] = all_records
        new_record = existing_record
    else:
        # 不存在旧记录，创建新记录
        new_record = {
            "id": news_id,
            "collection": all_records
        }
    
    # 更新或插入记录
    updated = False
    for i in range(len(records)):
        if records[i].get("id") == news_id:
            records[i] = new_record
            updated = True
            break
    
    if not updated:
        records.append(new_record)
    
    # 重新写入JSONL文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    