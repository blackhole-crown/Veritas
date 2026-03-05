import json
import torch
import numpy as np
import random
import sys
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from langchain_community.embeddings import HuggingFaceEmbeddings, HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS

import argparse
parser = argparse.ArgumentParser(description='manual to this script')
parser.add_argument("--with_or_without_info", type=str)
args = parser.parse_args()
with_or_without_info = args.with_or_without_info


# os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'

dirs = ["..", 'create_prompt_llm/']
for _dir in dirs:
    if _dir not in sys.path:
        sys.path.append(_dir)

import covmis, liar2, prompt_rag
data_test = covmis.load_data('test')
data_entire = covmis.load_data('entire')
data_search = covmis.load_data_search('entire', None)

from swift.llm import (
    ModelType, get_vllm_engine, get_default_template_type,
    get_template, inference_vllm, VllmGenerationConfig
)
from custom import CustomModelType

if __name__ == '__main__':
    def set_seed(seed=42):
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)
        torch.backends.cudnn.deterministic = True
    set_seed()
    model_type = CustomModelType.llama_3_70b_instruct_awq

    model_kwargs = {'device': 'cuda:2'}
    encode_kwargs = {'normalize_embeddings': True} # set True to compute cosine similarity
    # query_instruction_for_rag = "Represent this sentence for searching relevant passages: "

    embedding_mxbai = HuggingFaceEmbeddings(
        model_name='/home/css/models/mxbai-embed-large-v1',
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )

    vector_store_norag = FAISS.load_local(
        "/home/hanlv/workspace/code/research/infodemic/LLM/lanchain/vector_store/db_faiss_related_articles_mxbai", 
        embedding_mxbai, allow_dangerous_deserialization=True)

    llm_engine = get_vllm_engine(
        model_type, 
        # torch_dtype=torch.float16,  # 检查正确的数据类型！！！！
        tensor_parallel_size=2,
        max_model_len=4096,
        gpu_memory_utilization=0.92,
        # model_id_or_path="/home/css/models/Mixtral-8x7B-Instruct-v0.1-GPTQ-int4",
        max_num_seqs=64,
        engine_kwargs = {
            # "enforce_eager": True,
            "seed": 42,
        }
    )

    template_type = get_default_template_type(model_type)
    template = get_template(template_type, llm_engine.hf_tokenizer)

    generation_config = VllmGenerationConfig(
        max_tokens=1, 
        temperature=0, 
        seed=42, 
        logprobs=20
    )

    get_resp_list = lambda request_list : inference_vllm(
        llm_engine, template, request_list, 
        generation_config=generation_config, 
        use_tqdm=True, 
    )

    import numpy as np
    K = 5



    def get_prompt_with_nothing(item):
        claim = item['claim']
        claim_date = item['date']
        pre = 'Please answer TRUE or FALSE. Below is a <CLAIM>. If the content described by the <CLAIM> is correct, then classify it as TRUE; if the content described by the <CLAIM> is incorrect, then classify it as FALSE.\n\n'
        text = f"<CLAIM>: {claim}\nPublication date: {claim_date}"

        return pre + text

    def get_prompt_with_OS(item, search_results):
        claim = item['claim']
        claim_date = item['date']
        pre = 'Please answer TRUE or FALSE. Below is some INFORMATION searched online and a <CLAIM>. Please classify the <CLAIM> as TRUE or FALSE based on the INFORMATION. If the content described by the <CLAIM> is correct, then classify it as TRUE; if the content described by the <CLAIM> is incorrect, then classify it as FALSE.\n\n'
        
        ids = slice(0, K)
        snippet = prompt_rag.get_brave_snippet(search_results, ids=ids)
        info = "INFORMATION:\n" + snippet + '\n'
        text = f"<CLAIM>: {claim}\nPublication date: {claim_date}"

        # print(pre + info + text)
        return pre + info + text

    # env: torch 
    def get_prompt_with_RA(item):
        claim = item['claim']
        claim_date = item['date']
        pre = 'Please answer TRUE or FALSE. Below is some KNOWN INFORMATION and a <CLAIM>. Please classify the <CLAIM> as TRUE or FALSE based on the KNOWN INFORMATION. If the content described by the <CLAIM> is correct, then classify it as TRUE; if the content described by the <CLAIM> is incorrect, then classify it as FALSE.\n\n'
        

        docs = vector_store_norag.similarity_search(claim, k=K)
        context = [doc.page_content for doc in docs]

        context_new = ""
        for i, item in enumerate(context):
            context_new += f"{i+1}. " + item + '\n'

        info = "KNOWN INFORMATION:\n" + context_new + '\n'
        text = f"<CLAIM>: {claim}\nPublication date: {claim_date}"

        # print(pre + info + text)
        return pre + info + text


    def get_label(response):
        """
        response -> label:

        TRUE. -> 2 and FALSE. -> 0

        """
        # 0:false, 2:true

        if response == "TRUE.":
            return 2
        elif response == "FALSE.":
            return 0
        else:
            raise Exception("Response既不是'TRUE.'，也不是'FALSE.'。")
            
    def get_ans(logprobs):
        p_true = -np.inf
        p_false = -np.inf

        TRUE = 21260
        FALSE = 31451
        logprob_true = logprobs.get(TRUE)
        logprob_false = logprobs.get(FALSE)
        if logprob_true is None and logprob_false is None:
            return None
        if logprob_true is not None:
            p_true = logprob_true.logprob
        if logprob_false is not None:
            p_false = logprob_false.logprob
        
        if p_true > p_false:
            return "TRUE."
        else:
            return "FALSE."

    def find_ind(idd):
        for i in range(len(data_entire)):
            if data_entire[i]["id"] == idd:
                return i
        return None

    request_list = []
    labels = []
    preds = []

    for item in data_test:
        if int(item["label"]) == 1:
            continue
        request_list.append({'query': get_prompt_with_nothing(
            item, # data_search[find_ind(item["id"])]["brave_search_results"]
        )})
        labels.append(item["label"])

    resp_list = inference_vllm(
        llm_engine, template, request_list,
        generation_config=generation_config, 
        use_tqdm=True, 
    )

    cnt = 0
    for i, resp in enumerate(resp_list):
        # print(f"query: {request['query']}")
        ans = get_ans(resp['logprobs'][0])
        if ans is None:
            cnt += 1
            if labels[i] == 0:
                preds.append(2)
            else:
                preds.append(0)
        else:
            preds.append(get_label(ans))
        # print(f"response: {resp['response']}")

    metric = (
        accuracy_score(labels, preds), 
        f1_score(labels, preds, average='macro'),
        precision_score(labels, preds, average='macro'), 
        recall_score(labels, preds, average='macro'))

    print(metric)
    print(cnt)


    def add_metrics(metrics, metric):
        metrics.append({
                "model": "Meta-Llama-3-70B-Instruct",
                "ACC": metric[0],
                "F1": metric[1],
                "Precision": metric[2],
                "Recall": metric[3]
            }
        )

    with open(f'test_metric_no_sft/covmis/version_paper/test/{with_or_without_info}/Meta-Llama-3-70B-Instruct(_llama3).json', 'r') as f:
        metrics = json.load(f)

    add_metrics(metrics, metric)
    with open(f'test_metric_no_sft/covmis/version_paper/test/{with_or_without_info}/Meta-Llama-3-70B-Instruct(_llama3).json', 'w') as f:
        json.dump(metrics, f, indent=4)


