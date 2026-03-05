from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import jsonlines, json
import os
from tqdm import tqdm
from datetime import datetime

def cal_metric_single_llm(
        inference_prepare, inference_functions, 
        sft_args, ckpt_dir, train_loss, save=True, use_vllm=False,
        data_dir=None, data_type='test'
):
    def load_metrics(file_dir, model_name, template_type):
        os.makedirs(file_dir, exist_ok=True)
        file_path = file_dir + '/' + f"{model_name}({template_type}).json"

        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump([], f, indent=4)
        with open(file_path, "r") as f:
            metrics:list = json.load(f)
        return metrics
    
    def save_metrics(file_dir, model_name, template_type, metrics, save):
        if save:
            file_path = file_dir + '/' + f"{model_name}({template_type}).json"
            with open(file_path, "w") as f:
                json.dump(metrics, f, indent=4)

    def update_metric_item(item, train_loss):
        """
        如果已经存在, 那么更新其缺少的信息: train_loss
        """
        do_update = False

        if item.get("train_loss") is None:
            do_update = True
            item["train_loss"] = train_loss
        return do_update
    
    def update_metrics(
            metrics, model_name, split_type, train_ratio, labels, preds, 
            search_date=None, lr=None
    ):
        new_item = {
            "model": model_name,
            # "train_data": dataset_name,
            "train_test_split": split_type,
            "train_ratio": train_ratio,
            "train_loss": train_loss,
        }
        
        if lr is not None:
            new_item.update(lr=lr)
        if search_date is not None:
            new_item.update(search_date=search_date)
        new_item.update(
            ACC=accuracy_score(labels, preds),
            F1=f1_score(labels, preds, average='macro'),
            Precision=precision_score(labels, preds, average='macro'),
            Recall=recall_score(labels, preds, average='macro'),
        )
        metrics.append(new_item)
        return new_item
    
    def get_with_or_without_info(train_dataset_path: str):
        with_or_without_info_list = [
            "with_info", "with_solar_info", "with_mixtral_info", 
            "with_llama3_info", "without_info"]
        search_engines = ["brave"]
        for with_or_without_info in with_or_without_info_list:
            if with_or_without_info in ["with_solar_info", "with_mixtral_info", "with_llama3_info"]:
                for search_engine in search_engines:
                    info_search = with_or_without_info + '/' + search_engine
                    if info_search in train_dataset_path:
                        return info_search
            else:
                if with_or_without_info in train_dataset_path:
                    return with_or_without_info
        raise Exception(f"with_or_without_info选择范围：{with_or_without_info_list}\nsearch_engines的选择范围：{search_engines}")
    
    def get_split_type(train_dataset_path: str):
        pos_colon = train_dataset_path.find(":")
        pos_slash_1 = train_dataset_path.rfind("/", 0, pos_colon)
        pos_slash_2 = train_dataset_path.find("/", pos_colon)
        split_types = f"{train_dataset_path[pos_slash_1+1:pos_colon]}:{train_dataset_path[pos_colon+1:pos_slash_2]}"
        return split_types
    
    def get_train_ratio(train_dataset_path: str):
        pos_train = train_dataset_path.find("/train_data_")
        if pos_train == -1:
            raise Exception("无法从训练数据路径中找到'/train_data_'")
        
        pos_end = train_dataset_path.find(".json", pos_train)
        return train_dataset_path[pos_train + len("/train_data_"): pos_end]
    
    def get_data_version(custom_train_dataset_path: str):
        pos_sub = custom_train_dataset_path.find("subtrain_data")
        if pos_sub == -1:
            raise Exception("无法从训练数据路径中找到'subtrain_data'")
        
        pos_end = custom_train_dataset_path.find("/", pos_sub)
        return custom_train_dataset_path[pos_sub + len("subtrain_data"): pos_end]
    
    def get_model_name(sft_args):
        model_id_or_path = sft_args.get("model_cache_dir", None)
        if model_id_or_path is None:
            model_id_or_path = sft_args["model_id_or_path"]
        return model_id_or_path[model_id_or_path.rfind('/') + 1:]
    
    def get_sft_type(sft_args):
        sft_type = sft_args["sft_type"]
        if sft_type == "lora":
            quantization_bit = sft_args["quantization_bit"]
            if sft_args.get('use_dora'):
                sft_type = "dora"
            elif sft_args.get("use_rslora"):
                sft_type = "rslora"
            elif sft_args.get("lora_lr_ratio") is not None:
                sft_type += "_plus"
            elif quantization_bit != 0:
                sft_type = f"qlora-int{quantization_bit}"
            elif sft_args.get("init_lora_weights") == "pissa":
                sft_type = "pissa"

        return sft_type
    
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
        
    def get_lr(output_dir: str):
        pos_lr = output_dir.find('lr=')
        if pos_lr == -1:
            raise Exception("无法从训练数据路径中找到'lr'")
        pos_end = output_dir.find("-20", pos_lr)
        return output_dir[pos_lr + len("lr="): pos_end]
    
    def show_val_info(model_name, sft_type, lr, train_loss):
        print(f'{model_name} sft_type={sft_type} lr={lr} train_loss={train_loss}')
        
    def get_claim(query):
        pos_claim = query.find("CLAIM: ") + len("CLAIM: ")
        return query[pos_claim:query.find('\nPRIOR KNOWLEDGE:', pos_claim)].strip()
    
    def save_wrong_claims(file_dir, model_name, sft_type, lr, cnt_wrong, wrong_claims):
        os.makedirs(file_dir, exist_ok=True)
        file_path = file_dir + '/' + f"{model_name}-lr={lr}.txt"
        
        with open(file_path, "w") as f:
            title = f'{model_name}, sft_type={sft_type}, lr={lr}, cnt_wrong={cnt_wrong}\n'
            f.writelines(('\n').join([title] + wrong_claims))

    def get_dataset_name(dataset_dir):
        pos_name = dataset_dir.find('my_data/')
        if pos_name == -1:
            raise Exception()
        pos_name += len('my_data/')
        pos_end = dataset_dir.find('/' + get_with_or_without_info(sft_args["dataset"][0]), pos_name)
        if pos_end == -1:
            dataset_name = "covmis"
        else:
            dataset_name = dataset_dir[pos_name:pos_end]
        return dataset_name
    
    with_or_without_info = get_with_or_without_info(sft_args["dataset"][0])
    split_type = get_split_type(sft_args["dataset"][0])
    train_ratio = get_train_ratio(sft_args["dataset"][0])
    data_version = get_data_version(sft_args["dataset"][0])
    model_name = get_model_name(sft_args)
    template_type = sft_args["template_type"]
    sft_type = get_sft_type(sft_args)
    lora_rank = sft_args["lora_rank"]
    vera_rank = sft_args["vera_rank"]
    num_train_epochs = sft_args["num_train_epochs"]

    lr = get_lr(sft_args["output_dir"])
    dataset_name = get_dataset_name(sft_args["dataset"][0])
    search_date = None
    
    assert data_type in ["test", "valid"], f'data_type error: {data_type}'
    
    if data_dir is None or data_dir == "":
        data_dir = f"../my_data/{dataset_name}/{with_or_without_info}/train_valid_split/{split_type}/\
{data_type}_data{data_version}.jsonl"
    else:
        dataset_name = get_dataset_name(data_dir)

        # if f"{data_type}" not in dataset_name:
        #     raise Exception()
        if "timeline" in data_dir:
            search_date = data_dir[-16:-6]
        # split_type = get_split_type(data_dir)
    
    assert dataset_name in ["liar2", "covmis", "liar2_wsc", "covmis_wsc", "covmis_wsc2"], "Error dataset name!!"


    data = []
    labels, preds = [], []
    with jsonlines.open(data_dir, 'r') as f:
        for item in f.iter():
            data.append(item)
    
    # 判断metric是否已经存在，那么不用再计算
    exist = False
    do_update = False

    base_dir = "/home/hanlv/workspace/code/research/infodemic/misinformation/CEMD/swift2/my_inferencing/"
    if train_ratio == "1.0":
        file_dir = base_dir + f"test_metric_single_llm/{dataset_name}/{data_type}/{with_or_without_info}/\
{dataset_name}_data{data_version}-split={split_type}-ratio={train_ratio}/{sft_type}"

        if sft_type == "adalora":
            r1, r2 = sft_args["adalora_target_r"], sft_args["adalora_init_r"]
            file_dir += f"-r={r1}_{r2}"
        elif sft_type == "vera":
            file_dir += f"-r={vera_rank}" 
        else:
            file_dir += f"-r={lora_rank}" 
        if search_date is not None:
            file_dir +=f"-lr={lr}-timeline"
        metrics = load_metrics(file_dir, model_name, template_type)
        for item in metrics:
            if item["train_test_split"] == split_type and \
                item["train_ratio"] == train_ratio and \
                    ((search_date is not None and item["search_date"] == search_date) or (search_date is None and item["lr"] == lr)):
                do_update = update_metric_item(item, train_loss)
                exist = True
                break
    else:
        file_dir = base_dir + f"test_metric_single_llm/{dataset_name}/{data_type}/{with_or_without_info}/\
{dataset_name}_data{data_version}-split={split_type}-sft={sft_type}-lr={lr}"
        metrics = load_metrics(file_dir, model_name, template_type)
        for item in metrics:
            if item["train_test_split"] == split_type and \
                item["train_ratio"] == train_ratio:

                do_update = update_metric_item(item, train_loss)
                exist = True
                break

    if exist:
        if do_update:
            save_metrics(file_dir, model_name, template_type, metrics, save=save)
        return

    wrong_queries = []
    wrong_claims = []
    cnt_wrong = 0
    if (not use_vllm) or model_name in [] or sft_type in ["adalora", "dora"]:
        # 使用 非vllm 推理
        model, template = inference_prepare[0]()
        inference = inference_functions[0]
        show_val_info(model_name, sft_type, lr, train_loss)

        progress_bar = tqdm(data, desc=f'{model_name} lr={lr}', total=len(data))

        
        for item in data:
            progress_bar.set_description(f'cnt_wrong={cnt_wrong}')
            progress_bar.update(1)  # Increment the progress bar

            query = item["query"]
            pred_raw = inference(model, template, query)[0].strip()
            label_raw = item["response"]

            labels.append(get_label(label_raw))
            preds.append(get_label(pred_raw))

            if labels[-1] != preds[-1]:
                
                wrong_queries.append(query)
                wrong_claims.append(f"Label: {label_raw} Pred: {pred_raw} Query:\n{query}" + '\n' + '*'*50 + '\n\n')
                cnt_wrong += 1
        progress_bar.close()
    else:
        # vllm 推理
        vllm_engine, template, generation_config, lora_request = inference_prepare[1](ckpt_dir)
        inference = inference_functions[1]
        show_val_info(model_name, sft_type, lr, train_loss)

        request_list = [{'query': i["query"]} for i in data]
        response_list = inference(
            vllm_engine, template, request_list, 
            generation_config=generation_config, 
            lora_request=lora_request,
            use_tqdm=True,
        )
        
        for item_data, item_resp in zip(data, response_list):
            query = item_data["query"]
            pred_raw = item_resp["response"]
            label_raw = item_data["response"]

            labels.append(get_label(label_raw))
            preds.append(get_label(pred_raw))

            if labels[-1] != preds[-1]:
                wrong_queries.append(item_data["query"])
                wrong_claims.append(f"Label: {label_raw} Pred: {pred_raw} \nClaim: {get_claim(query)}\n")
                cnt_wrong += 1
    # ratio为1.0
    if train_ratio == "1.0":
        new_metric = update_metrics(
            metrics, model_name, split_type, train_ratio, 
            labels=labels, preds=preds, search_date=search_date, lr=lr
        )
        if search_date is None:
            metrics.sort(key=lambda x: (x["train_test_split"], x["train_ratio"], float(x["lr"])))
        else:
            metrics.sort(key=lambda x: (x["train_test_split"], x["train_ratio"], datetime.strptime(x['search_date'], '%Y-%m-%d')))
        # save_metrics(file_dir, model_name, template_type, metrics, save=save)

    else:
        # 不同的ratio
        new_metric = update_metrics(
            metrics, model_name, split_type, train_ratio,
            labels=labels, preds=preds, 
        )
        metrics.sort(key=lambda x: (x["train_test_split"], x["train_ratio"]))
    
    save_metrics(file_dir, model_name, template_type, metrics, save=save)
    print(json.dumps(new_metric, indent=4))
    
    # save query
    # with open("wrong_ans.txt", "a") as f:
    #     title = f'{model_name}, sft_type={sft_type}, lr={lr}, wrong={cnt_wrong}'
    #     f.writelines(('\n\n' + '-' * 300 + '\n\n').join([title] + wrong_ans))

    # save_wrong_claims(file_dir, model_name, sft_type, lr, cnt_wrong, wrong_claims)

    return labels, preds

    
