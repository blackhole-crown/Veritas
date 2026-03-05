import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

import utils.brave_search as brave_search
import utils.graphrag as grag
import utils.utils as utils
import utils.sql as sql
import pandas as pd
import time
import json

class GlobalVars:
    K = utils.DEFUALT_K
    data_table = grag.get_data_table_init()
    data_table_selected = grag.DataTableKey.community_reports
    query_table_selected = K
    query_history = []  #[]
    split_contexts = utils.split_contexts


def get_query_coe(news):
    Q = f"You are now required to classify the following NEWS. Please present a **chain of evidence** as outlined above, and provide a definitive judgment result (TRUE or FALSE, wrapped in **).\n\
NEWS: **{news}**"
    
    return Q


def chat(message, result_id, history):

    history = history or []                 #如果 history 是 None 或为空，则将其初始化为一个空列表
    message = message.strip()               #去除 message 的首尾空白字符
    query_date = utils.get_today()          #获取当前日期

    if message != '':
        
        print("The claim is: " + message)
        # print("Doing orinal judgement...")
        # utils.origin_judge(message,query_date,GlobalVars.K)
        
        print("Searching contexts online...")
        search_res, news_id, last_output = brave_search.get_brave_search(       #调用 brave_search.get_brave_search 方法，传入 message, query_date 和 GlobalVars.K，用来进行在线搜索。
        message, query_date, GlobalVars.K)                                     #返回值包括：search_res: 搜索结果。news_id: 相关新闻的 ID。last_output: 上一次的输出结果。                        
 
         
        print("Buiding graph knowledge...")
        GlobalVars.data_table = grag.build_graph(#                              #调用 grag.build_graph 方法，用搜索结果 search_res 和其他参数构建知识图谱，并将结果存储到全局变量 GlobalVars.data_table 中
            search_res, news_id, GlobalVars.K, last_output, GlobalVars.split_contexts)


        print("Building a chain of evidence...")
        res_coe = grag.get_COE(message, news_id, GlobalVars.K, last_output)     #调用 grag.get_COE 方法，生成证据链（Chain of Evidence），返回值存储在变量 res_coe 中。 
        
        update = (lambda x: False if x is not None else True)(last_output)
        
        GlobalVars.query_history = utils.update_query_history(                  #调用 utils.update_query_history 方法，更新查询历史记录（GlobalVars.query_history），传入相关参数包括新闻 ID、当前日期、证据链等
            news_id, query_date, res_coe, GlobalVars.K, update=update)
        print("Success!")
        
        if result_id != 0:
            sql.insert_result(result_id,message)
            sql.insert_cite_references(result_id,message)
        
        response = res_coe                                                      #将生成的证据链（res_coe）作为助手的响应内容
    else:
        time.sleep(2)
        response = message
        
    history.append({"role": "user", "content": message})                        #将用户消息和助手响应以字典的形式分别添加到聊天记录 history 中
    history.append({"role": "assistant", "content": response})
    
    return history, history

def read_claims_from_jsonl(file_path):
    claims = []

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # 跳过空行
            if not line.strip():
                continue
                
            # 解析每行的JSON数据
            entry = json.loads(line.strip())
            
            # 如果需要有ID筛选条件，可以取消注释下面的代码
            # if int(entry['id'])< 150 :
            claims.append(str(entry['summary']))
    
    return claims

def chat_test(message, result_id, history):
    
    chat(message, result_id, history)
    
    
    
if __name__=='__main__':
    
    
    jsonl_file_path = '/home/zhouzehui/workspace/data/xxx.jsonl'  #todo学长给的
    claims = read_claims_from_jsonl(jsonl_file_path)
    
    # for claim in claims:
    #     chat(claim,0,None)
    
    

    chat("沃尔玛跻身万亿美元序列：传统零售大佬，悄悄变身科技卷王.",0,None)
    