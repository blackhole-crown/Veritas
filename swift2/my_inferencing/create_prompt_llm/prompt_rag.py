import json
from tqdm import tqdm
from datetime import datetime
import jsonlines
import os
import subprocess
import shutil
import sys
import re

dirs = ["../..", ".."]
for _dir in dirs:
    if _dir not in sys.path:
        sys.path.append(_dir)

import covmis, liar2

# def get_claim_with_date_old(claim, claim_date=None):
#     if claim_date is None:
#         return  claim
    
#     res = "\n"
#     res += "Publication date: " + claim_date + '\n' + "Content: " + claim
#     return res

def get_claim_with_date(claim, claim_date=None, claimant=None):
    if claim_date is None and claimant is None:
        return claim
    
    res = claim
    if claimant is not None:
        res += "\nClaimant: " + claimant
    if claim_date is not None:
        res += "\nPublication date: " + claim_date
    return res

def get_bing_snippet(bing_search_results, K=5, claim_date=None):
    if bing_search_results.get("webPages") is None:
        return ""
    
    results = bing_search_results["webPages"]["value"]
    snippets = [i["snippet"] for i in results][:K]

    snippet = ""

    for i, item in enumerate(snippets):
        snippet += f"{i+1}. " + item + '\n'

    return snippet

def get_bing_snippet_v2(bing_search_results, K, claim_date, sort):
    """包含发布时间"""

    
    def get_snippets_dates(results, K=K):
        """找K个与claim发布时间最近的结果"""
        
        date_format = "%Y-%m-%d"
        date_claim = datetime.strptime(claim_date, date_format)
        
        if not sort:
            snippets = [i["snippet"] for i in results[:K]]
            dates = [i["datePublished"][:10] if i.get("datePublished") else "None" for i in results[:K]]
            return snippets, dates
        else:
            max_k = 20
            if K > max_k:
                raise Exception(f"K不能超过{max_k}")
            id_delta_list = [] # (id, delta): sinppet ID和snippet与claim发布日期的差
            results_10 = []
            need_supplement = False
            for i in results:
                if i.get("datePublished") is not None:
                    results_10.append(i)
                
                if len(results_10) == max_k:
                    break
            if len(results_10) < K:
                need_supplement = True

            for id, item in enumerate(results_10):
                date_item = datetime.strptime(item["datePublished"][:10], date_format)
                delta = abs((date_item - date_claim).days)

                id_delta_list.append((id, delta))

            id_delta_list_sorted = sorted(id_delta_list, key=lambda x: x[1])

            # print(id_delta_list_sorted)
            snippets = [results_10[i[0]]["snippet"] for i in id_delta_list_sorted[:K]]
            dates = [results_10[i[0]]["datePublished"][:10] for i in id_delta_list_sorted[:K]]

            if need_supplement:
                for i, item in enumerate(results):
                    if i in [x[0] for x in id_delta_list_sorted]:
                        continue
                    
                    snippets.append(item["snippet"])
                    dates.append("None")
                    if len(snippets) == K:
                        break

            return snippets, dates

    if bing_search_results.get("webPages") is None:
        return ""
    
    results = bing_search_results["webPages"]["value"]
    snippets, dates = get_snippets_dates(results)

    snippet = ""

    for i, item in enumerate(snippets):
        snippet += f"{i+1}.\n" + "Publication date: " + dates[i] + '\n' + "Content: " + item + '\n'

    return snippet

def get_brave_snippet(search_results, ids: slice | list, ret_type='str', max_len=None):
    """
    max_len 为 content 中每一个段的最大长度
    """
    def get_truncat_snippets(extra_snippets, max_len):
        snippets_truncat = []
        for snippet in extra_snippets:
            snippet_tokenized = snippet.split()
            snippets_truncat.append(' '.join(snippet_tokenized[:max_len]))
        return snippets_truncat

    results = search_results["web"]["results"]
    snippet = ""
    snippets = []
    if isinstance(ids, slice):
        results_filtered = results[ids]
        id_start = ids.start
    elif isinstance(ids, list):
        results_filtered = [results[i] for i in ids]
        id_start = 0
    else:
        raise Exception()
    
    for i, item in enumerate(results_filtered):

        date = item.get("page_age", "None")
        if date != "None":
            date = date[:10]

        extra_snippets = item.get("extra_snippets")
        if max_len is not None and extra_snippets is not None:
            extra_snippets = get_truncat_snippets(extra_snippets, max_len)
        if extra_snippets:
            content = "\n".join(extra_snippets)
        else:
            content = item["description"]

        one_info = f"Information {id_start + i + 1}:\n" + "Publication date: " + date + '\n' + \
            "Title: " + item["title"] + '\n' + "Content:\n" + content + '\n'
        
        if ret_type == 'str':
            snippet += one_info
        elif ret_type == 'list':
            snippets.append(one_info.strip())
        else:
            raise Exception('返回类型只能从 str 与 list 中选取！')
        
    if ret_type == "str":
        return snippet
    else:
        return snippets

def get_prompt_for_generating_prior_knowledge_old(
        claim, claim_date, search_engine, search_results, model_name,
        K=5, sort=False, ids=None, without_info=False, without_claim_date=False):
    """
    sort: 对search result 按时间进行排序
    """

    claim = claim.strip()

    if model_name == "solar":
        pre = "Below is some INFORMATION searched online and a CLAIM. These pieces of INFORMATION are relevant to the CLAIM. This CLAIM and all INFORMATION include their respective publication dates and contents. To classify the CLAIM more accurately (if the content described by the CLAIM is correct, it will be classified as TRUE; if the content described by the CLAIM is incorrect, it will be classified as FALSE), please first expand on the given INFORMATION and provide a detailed summary of it. Then analyze, reason, and provide reasonable evidence to judge the correctness of the CLAIM based on the available information and your knowledge, and finally generate prior knowledge that helps classify the CLAIM.\n\n"
    elif model_name == "mixtral":
        # v1
        # pre = "Below is some INFORMATION searched online and a CLAIM. These pieces of INFORMATION are relevant to the CLAIM. This CLAIM and all INFORMATION include their respective publication dates and contents. To classify the CLAIM more accurately (if the content described by the CLAIM is correct, it will be classified as TRUE; if the content described by the CLAIM is incorrect, it will be classified as FALSE), please first provide a detailed summary of the given INFORMATION. Then reason, and provide reasonable evidence to judge the correctness of the CLAIM based on the available information and your knowledge. In reasoning, it is necessary to consider the sequential relationship between the date of publication of the CLAIM and the date of publication of the INFORMATION.\n\n"
        pre = "Below is some INFORMATION searched online and a CLAIM. These pieces of INFORMATION are relevant to the CLAIM. This CLAIM and all INFORMATION include their respective publication dates and contents. To classify the CLAIM more accurately (if the content described by the CLAIM is correct, it will be classified as TRUE; if the content described by the CLAIM is incorrect, it will be classified as FALSE), please first provide a detailed summary of the given INFORMATION and restate the CLAIM. Then reason, and provide reasonable evidence to judge the correctness of the CLAIM based on the available information and your knowledge. In reasoning, it is necessary to consider the sequential relationship between the date of publication of the CLAIM and the date of publication of the INFORMATION.\n\n"
    else:
        raise Exception("model_name 只能从solar，mixtral中选择")
    
    if without_claim_date:
        text = "CLAIM: " + claim
    else:
        text = "CLAIM:" + get_claim_with_date(claim, claim_date)

    if search_engine == "bing":
        snippet = get_bing_snippet_v2(search_results, K=K, claim_date=claim_date, sort=sort)
    elif search_engine == "brave":
        if ids is None:
            ids = slice(0, K)
        snippet = get_brave_snippet(search_results, ids=ids)
    else:
        raise Exception("Select search engines in [\"bing\", \"brave\"].")
    
    info = "INFORMATION:\n" + snippet + '\n'

    if without_info:
        return (pre + text).strip()
    else:
        return pre + info + text

def get_prompt_for_generating_prior_knowledge(
        claim, claim_date, search_engine, search_results, model_name,
        K=5, claimant=None, sort=False, ids=None, without_info=False, without_claim_date=False, n_truncate=0):
    """
    pre + info + text
    """

    claim = claim.strip()

    if model_name == "solar":
        pre = "Below is some INFORMATION searched online and a CLAIM. These pieces of INFORMATION are relevant to the CLAIM. This CLAIM and all INFORMATION include their respective publication dates and contents. To classify the CLAIM more accurately (if the content described by the CLAIM is correct, it will be classified as TRUE; if the content described by the CLAIM is incorrect, it will be classified as FALSE), please first expand on the given INFORMATION and provide a detailed summary of it. Then analyze, reason, and provide reasonable evidence to judge the correctness of the CLAIM based on the available information and your knowledge, and finally generate prior knowledge that helps classify the CLAIM.\n\n"
        # pre = "Below is some INFORMATION searched online and a CLAIM. These pieces of INFORMATION are relevant to the CLAIM. This CLAIM and all INFORMATION include their respective publication dates and contents. To classify the CLAIM more accurately (if the content described by the CLAIM is correct, it will be classified as TRUE; if the content described by the CLAIM is incorrect, it will be classified as FALSE), please first provide a clear summary of the given INFORMATION, and provide reasonable evidence to judge the correctness of the CLAIM based on the available information and your knowledge.\n\n"
    elif model_name == "mixtral":
        # pre = "Below is a CLAIM and some INFORMATION searched online. These pieces of INFORMATION are relevant to the CLAIM. This CLAIM and all INFORMATION include their respective publication dates and contents. To classify the CLAIM more accurately (if the content described by the CLAIM is correct, it will be classified as TRUE; if the content described by the CLAIM is incorrect, it will be classified as FALSE), please first provide a detailed summary of the given INFORMATION and restate the CLAIM. Then reason, and provide reasonable evidence to judge the correctness of the CLAIM based on the available information and your knowledge. In reasoning, it is necessary to consider the sequential relationship between the date of publication of the CLAIM and the date of publication of the INFORMATION.\n\n"
        pre = "Below is some INFORMATION searched online and a CLAIM. These pieces of INFORMATION are relevant to the CLAIM. This CLAIM and all INFORMATION include their respective publication dates and contents. To classify the CLAIM more accurately (if the content described by the CLAIM is correct, it will be classified as TRUE; if the content described by the CLAIM is incorrect, it will be classified as FALSE), please first provide a clear summary of the given INFORMATION, and provide reasonable evidence to judge the correctness of the CLAIM based on the available information and your knowledge.\n\n"
        
        # pre = "Below is some INFORMATION searched online and a <CLAIM>. These pieces of INFORMATION are relevant to the <CLAIM>. This <CLAIM> and all INFORMATION include their respective publication dates and contents. To classify the <CLAIM> more accurately (if the content described by the <CLAIM> is correct, it will be classified as TRUE; if the content described by the <CLAIM> is incorrect, it will be classified as FALSE), please first provide a clear summary of the given INFORMATION, and provide reasonable evidence to judge the correctness of the <CLAIM> based on the available information and your knowledge.\n\n"
    
    elif model_name == "llama3":
        # pre = "Below is some INFORMATION searched online and a <CLAIM>. These pieces of INFORMATION are relevant to the <CLAIM>. This <CLAIM> and all INFORMATION include their respective publication dates and contents. To classify the <CLAIM> more accurately (if the content described by the <CLAIM> is correct, it will be classified as TRUE; if the content described by the <CLAIM> is incorrect, it will be classified as FALSE), please first provide a clear summary of the given INFORMATION, restate the <CLAIM>, and provide reasonable evidence to judge the correctness of the <CLAIM> based on the available information and your knowledge.\n\n"
        pre = "Below is some INFORMATION searched online and a <CLAIM>. These pieces of INFORMATION are relevant to the <CLAIM>. This <CLAIM> and all INFORMATION include their respective publication dates and contents. To classify the <CLAIM> more accurately (if the content described by the <CLAIM> is correct, it will be classified as TRUE; if the content described by the <CLAIM> is incorrect, it will be classified as FALSE), please first provide a clear summary of the given INFORMATION, and provide reasonable evidence to judge the correctness of the <CLAIM> based on the available information and your knowledge.\n\n"
    
    else:
        raise Exception("model_name 只能从solar，mixtral中选择")
    
    if without_claim_date:
        text = "CLAIM: " + claim
    else:
        if model_name == "solar":
            text = "CLAIM: "
        if model_name == "mixtral":
            text = "CLAIM: "
        elif model_name == "llama3":
            text = "<CLAIM>: "
        text += get_claim_with_date(claim, claim_date, claimant)

    if search_engine == "bing":
        snippet = get_bing_snippet_v2(search_results, K=K, claim_date=claim_date, sort=sort)
    elif search_engine == "brave":
        if ids is None:
            ids = slice(0, K)
        snippet = get_brave_snippet(search_results, ids=ids)
        if n_truncate > 0:
            snippet = snippet[:-n_truncate]
    else:
        raise Exception("Select search engines in [\"bing\", \"brave\"].")
    
    info = "INFORMATION:\n" + snippet + '\n'
    
    if without_info:
        return (pre + text).strip()
    else:
        return pre + info + text

def get_prompts_for_summarize_snippets(
        claim, claim_date, search_engine, search_results, K=5
):
    """
    以5条信息作为一个分组

    [0:5], [5:10], [5:15], [15:20]
    """
    slices_tmp = [slice(0, 5), slice(5, 10), slice(10, 15), slice(15, 20)]
    slices = []
    id_slices = None
    K = min(K, len(search_results["web"]["results"]))
    for i, _slice in enumerate(slices_tmp):
        if K-1 >= _slice.start and K - 1 < _slice.stop:
            id_slices = i
            break
    for i in range(id_slices + 1):
        if i < id_slices:
            slices.append(slices_tmp[i])
        else:
            slices.append(slice(slices_tmp[i].start, K))
    prompts = []
    claim = claim.strip()
    # pre = "Below is a CLAIM and some INFORMATION searched online. These pieces of INFORMATION are relevant to the CLAIM. This CLAIM and all INFORMATION include their respective publication dates and contents. To classify the CLAIM more accurately (if the content described by the CLAIM is correct, it will be classified as TRUE; if the content described by the CLAIM is incorrect, it will be classified as FALSE), please provide a detailed summary of each piece of INFORMATION given.\n\n"
    pre = "Please provide a detailed summary of each piece of information below"
    # pre = "Please summarize the information"
    # text = "CLAIM:" + get_claim_with_date(claim, claim_date) +'\n\n'

    for _slice in slices:
        if search_engine == "bing":
            snippet = get_bing_snippet_v2(search_results, K=K, claim_date=claim_date)
        elif search_engine == "brave":
            snippet, cnt = get_brave_snippet(search_results, ids=_slice, claim_date=claim_date)
        else:
            raise Exception("Select search engines in [\"bing\", \"brave\"].")
    
        info = "INFORMATION:\n" + snippet

        # prompts.append(pre + text + info)
        prompts.append(pre + f"(from No.{_slice.start + 1} to No.{_slice.start + cnt}).\n\n" + snippet)
    return prompts

def get_prompt_for_generating_prior_knowledge_by_summary(claim, claim_date, summary: list, K):
    
    if K == 5:
        _n = 1
    elif K == 10:
        _n = 2
    elif K == 15:
        _n = 3
    elif K == 20:
        _n = 4
    else:
        raise Exception()
    
    claim = claim.strip()
    pre = "Below is a claim and some information related to it. To classify the claim more accurately (if the content described by the claim is correct, it will be classified as TRUE; if the content described by the claim is incorrect, it will be classified as FALSE), please analyze, reason, and provide reasonable evidence to judge the correctness of the claim based on the available information and your knowledge, and finally generate prior knowledge that helps classify the claim.\n\n"

    text = "Claim:" + get_claim_with_date(claim, claim_date) +'\n\n'

    info = "Information:\n" + "\n\n".join(summary[:_n]).strip()

    return pre + text + info


# def get_prompt_with_prior_knowledge_old(
#         claim, search_engine, search_results, 
#         prior_knowledge, K=5, claim_date=None, sort=False, known_info=True, ids=None):
#     """
#     task + claim(with date) + prior knowledge with information

#     sort: 对search result 按时间进行排序
    
#     known_info: prior knowledge中是否包含已知信息
#     """
#     claim = claim.strip()
#     pre = "According to the CLAIM and the PRIOR KNOWLEDGE, please classify the CLAIM as TRUE or FALSE. If the content described by the CLAIM is correct, then classify it as TRUE; if the content described by the CLAIM is incorrect, then classify it as FALSE.\n\n"
#     text = "CLAIM:" + get_claim_with_date(claim, claim_date) +'\n\n'

#     if search_engine == "bing":
#         snippet = get_bing_snippet_v2(search_results, K=K, claim_date=claim_date, sort=sort)
#     elif search_engine == "brave":
#         if ids is None:
#             ids = slice(0, K)
#         snippet = get_brave_snippet(search_results, ids=ids)
#     else:
#         raise Exception("Select search engines in [\"bing\", \"brave\"].")

#     if known_info:
#         return pre + text + "PRIOR KNOWLEDGE:\n" + snippet + '\n' + prior_knowledge.strip()
#     else:
#         return pre + text + "PRIOR KNOWLEDGE:\n" + prior_knowledge.strip()

def get_claim_id(claim, data_search):
    """
    非原始数据中的claim id，获取的是claim的位次编号
    """
    for i in range(len(data_search)):
        if claim.strip() in data_search[i]["claim"].strip():
            return i

def get_prompt_with_prior_knowledge(
        claim, search_engine, search_results, 
        prior_knowledge, K=5, claim_date=None, claimant=None, justification=None,
        known_info=True, rag_info=True, justify_info=False, 
        ids=None):
    """
    task + claim(with date) + prior knowledge

    sort: 对search result 按时间进行排序
    
    known_info: prompt是否包含已知信息
    """
    if justify_info and justification is None:
        raise Exception("只有LIAR2才能使用justify_info")
    
    claim = claim.strip()
    pre = "Below is a CLAIM and the PRIOR KNOWLEDGE associated with it. Please classify the CLAIM as TRUE or FALSE based on the PRIOR KNOWLEDGE. If the content described by the CLAIM is correct, then classify it as TRUE; if the content described by the CLAIM is incorrect, then classify it as FALSE.\n\n"
    text = "CLAIM: " + get_claim_with_date(claim, claim_date, claimant) +'\n\n'

    if search_engine == "brave":
        if ids is None:
            ids = slice(0, K)
        snippet = get_brave_snippet(search_results, ids=ids)
    else:
        raise Exception("Select search engines in [\"brave\"].")

    # if known_info:
    #     return pre + text + "PRIOR KNOWLEDGE:\n" + snippet + '\n' + prior_knowledge.strip()
    # else:
    #     return pre + text + "PRIOR KNOWLEDGE:\n" + prior_knowledge.strip()
    
    if justify_info:
        assert not(known_info or rag_info), "justification 不能与 已知信息 和 rag信息 同时存在"

        return pre + text + "PRIOR KNOWLEDGE:\n" + justification.strip()
    else:
        if known_info and rag_info:
            return pre + text + "PRIOR KNOWLEDGE:\n" + snippet + '\n' + prior_knowledge.strip()
        elif rag_info:
            return pre + text + "PRIOR KNOWLEDGE:\n" + prior_knowledge.strip()
        elif known_info:
            return pre + text + "PRIOR KNOWLEDGE:\n" + snippet
        else:
            raise Exception()

def get_claim_id(claim, data_search):
    """
    非原始数据中的claim id，获取的是claim的位次编号
    """
    for i in range(len(data_search)):
        if claim.strip() in data_search[i]["claim"].strip():
            return i
        
# def save_search_llm(x, search_engine):
#     with open(f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS-2024/train_{search_engine}_search_llm.json", "w") as f:
#         json.dump(x, f, indent=4)

# def save_search_summary(x, search_engine):
#     with open(f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS-main/data/train_{search_engine}_search_summary.json", "w") as f:
#         json.dump(x, f, indent=4)

def save_search_llm_tmp(x, dataset, data_type, search_date):
    with open(f"data_search_llm_tmp_{dataset}_{data_type}_{search_date}.json", "w") as f:
        json.dump(x, f, indent=4)

def load_search_llm_tmp(dataset, data_type, search_date):
    try:
        with open(f"data_search_llm_tmp_{dataset}_{data_type}_{search_date}.json", "r") as f:
            return json.load(f)
    except:
        return []

# def save_search_summary_part(x, part):
#     with open(f"train_search_summary_v{part}.json", "w") as f:
#         json.dump(x, f, indent=4)

# def load_search_summary_part(part):
#     try:
#         with open(f"train_search_summary_v{part}.json", "r") as f:
#             return json.load(f)
#     except:
#         return []
    
def update_train_search_llm(
        model_name, get_resp_list, search_engine, dataset, prior_knowledge_version,
        data_type, search_date, 
        data_version=None, K=5, sort=False, use_random=False, wsc_version='none', save2_data_llm=False):
    data_llm_tmp = []
    # len_data_search_llm = len(data_search_llm)
    
    if dataset == "covmis":
        data = covmis.load_data(data_type, version=data_version)
        data_search =  covmis.load_data_search(
            data_type, search_date, version=data_version, search_engine=search_engine)
        data_llm =  covmis.load_data_llm(
            data_type, search_date, version=data_version, search_engine=search_engine)
        claim_key = 'claim'
        claimant_key = 'None'
        save_search_llm = lambda data: covmis.save_data_llm(
            data, data_type, search_date, version=data_version, search_engine=search_engine)
    elif dataset == "liar2":
        data = liar2.load_data(data_type)
        data_search = liar2.load_data_search(data_type, search_engine)
        data_llm = liar2.load_data_llm(data_type, search_engine)
        claim_key = 'statement'
        claimant_key = 'None' # 不用 claimant
        # save_search = lambda data: liar2.save_data_search(
        #     data, data_type, search_engine)
    else:
        raise Exception("数据集错误")

    prompt_list = []
    id_list = []

    data_llm_key = f"prior_knowledge_{model_name}_v{prior_knowledge_version}_K={K}"

    assert wsc_version in ["none", "1", "2"], f"Error wsc version: {wsc_version}!"

    if wsc_version != 'none':
        claim_key += '_wsc'
        data_llm_key += '_wsc'
        dataset += '_wsc'
        if int(wsc_version) > 1:
            claim_key += f'{wsc_version}'
            data_llm_key += f'{wsc_version}'
            dataset += f'{wsc_version}'

    for i in range(len(data_search)):
        if data[i]["id"] != data_search[i]["id"]:
            raise Exception("data_train 与 data 的 id 不匹配！")
        
        if data_llm[i].get(data_llm_key) is not None:
            continue

        if use_random:
            if K != 5 or sort:
                raise Exception()
            ids = data_search[i]["random_ids"]
        else:
            ids = None

        prompt = get_prompt_for_generating_prior_knowledge(
            data[i][claim_key], data[i]["date"], 
            search_engine, data_search[i][f"{search_engine}_search_results"], 
            model_name, K=K, claimant=data[i].get(claimant_key), sort=sort, ids=ids
        )
        prompt_list.append(prompt)
        id_list.append(data[i]["id"])

    if len(prompt_list) == 0:
        return 
    request_list = [{'query': prompt} for prompt in prompt_list]
    resp_list = get_resp_list(request_list)
    resp_list = [i["response"] for i in resp_list]

    with jsonlines.open(f"resp_list_{dataset}_{data_type}.jsonl", mode="w") as file_jsonl:
        for item in resp_list:
            file_jsonl.write(item)

    if save2_data_llm:
        i_resp = 0
        for i in range(len(data_llm)):
            if data_llm[i].get(data_llm_key) is not None:
                continue
            
            if id_list[i_resp] != data_llm[i]["id"]:
                raise Exception()
            
            data_llm[i][data_llm_key] = resp_list[i_resp].strip()
            i_resp += 1
        save_search_llm(data_llm)
    else: # save 2 tmp
        i_resp = 0
        for i in range(len(data_search)):
            if data_llm[i].get(data_llm_key) is not None:
                continue
            
            if id_list[i_resp] != data_search[i]["id"]:
                raise Exception()
            
            item_llm = {}
            item_llm["id"] = data_search[i]["id"]
            item_llm[f"prior_knowledge_{model_name}"] = resp_list[i_resp].strip()
            data_llm_tmp.append(item_llm)
            i_resp += 1
        save_search_llm_tmp(data_llm_tmp, dataset, data_type, search_date)

# def update_train_search_summary(
#         model, model_name, port, search_engine, data_search, part, K=20):
#     data_search_summary = load_search_summary_part(part)
#     for i in tqdm(range(len(data_search_summary), len(data_search))):
#         item = data_search[i]
#         item_summary = {}
        
#         # print(item["claim"])
#         item_summary["claim"] = item["claim"]
#         res = []
#         prompts = get_prompts_for_summarize_snippets(
#             item["claim"], item["date"], search_engine, item[f"{search_engine}_search_results"], K=K)
#         for prompt in prompts:
#             res_tmp = al.get_response(prompt, model, cache_seed=None, port=port)
#             res.append(res_tmp.strip())
        
#         item_summary[f"summary_{model_name}"] = res
        
#         data_search_summary.append(item_summary)

#         if i % 5 == 0:
#             save_search_summary_part(data_search_summary, part)

#     save_search_summary_part(data_search_summary, part)

# def update_train_search_llm_by_summary(
#         model, model_name, port, 
#         data_search_summary, summary_version, part, K=5):
    
#     assert K in [5, 10, 15, 20], "请从K只能为5, 10, 15, 20。"

#     data_search_llm = load_search_llm_part(part)
#     for i in tqdm(range(len(data_search_llm), len(data_search_summary))):
#         item = data_search_summary[i]
#         item_llm = {}
        
#         item_llm["claim"] = item["claim"]
#         prompt = get_prompt_for_generating_prior_knowledge_by_summary(
#             item["claim"], item["date"], item[f"summary_solar_v{summary_version}"], K=K)
        
#         item_llm[f"prior_knowledge_by_summary_{model_name}"] = al.get_response(prompt, model, cache_seed=None, port=port)
#         data_search_llm.append(item_llm)

#         if i % 20 == 0:
#             save_search_llm_part(data_search_llm, part)

#     save_search_llm_part(data_search_llm, part)

