import json

version_list = ["2", "2024", "original"]

type_list = ["train", "valid", "test", "entire"]
def get_data_dir(version, data_type):
    if data_type == "entire":
        return "/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS2/data.json"
    else:
        return f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS2/training{version}/{data_type}.json"

def get_data_llm_dir(version, data_type, search_date, search_engine="brave"):
    if data_type == "entire":
        return f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS2/data_{search_engine}_search_llm.json"
    else:
        if search_date is None:
            return f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS2/training{version}/{data_type}_{search_engine}_search_llm.json"
        else:
            return f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS2/training{version}/{data_type}_{search_engine}_search_llm/{search_date}.json"

def get_data_search_dir(version, data_type, search_date, search_engine="brave"):
    if data_type == "entire":
        return f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS2/data_{search_engine}_search.json"
    else:
        if search_date is None:
            return f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS2/training{version}/{data_type}_{search_engine}_search.json"
        else:
            return f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS2/training{version}/{data_type}_{search_engine}_search/{search_date}.json"


def load_data(data_type, version="2024"):
    """
    版本选择："2024" or "original"
    type: train, valid, test, entire
    """
    assert data_type in type_list, f"data_type需要从{type_list}中选择！"

    if version == "2024" or version == "2":
        with open(get_data_dir(version, data_type), "r") as f:
            return json.load(f)
    elif version == "original":
        if data_type != 'entire':
            raise Exception("original covmis的data type只能为entire!")
        with open("/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS2/data.json", "r") as f:
            return json.load(f)
    else:
        raise Exception(f"version需要从{version_list}中选择！")

def save_data(data, data_type, version="2024"):
    assert data_type in type_list, f"data_type需要从{type_list}中选择！"

    if version == "2024" or version == "2":
        with open(get_data_dir(version, data_type), "w") as f:
            json.dump(data, f, indent=4)
    else:
        raise Exception()
    
def load_data_llm(data_type, search_date, version="2024", search_engine="brave"):
    assert data_type in type_list, f"data_type需要从{type_list}中选择！"

    if (version == "2024" or version == "2") and search_engine == "brave":
        with open(get_data_llm_dir(version, data_type, search_date, search_engine), "r") as f:
            return json.load(f)
    else:
        raise Exception()

def save_data_llm(data, data_type, search_date, version="2024", search_engine="brave"):
    assert data_type in type_list, f"data_type需要从{type_list}中选择！"

    if (version == "2024" or version == "2") and search_engine == "brave":
        with open(get_data_llm_dir(version, data_type, search_date, search_engine), "w") as f:
            json.dump(data, f, indent=4)
    else:
        raise Exception()

def load_data_search(data_type, search_date, version="2024", search_engine="brave"):
    assert data_type in type_list, f"data_type需要从{type_list}中选择！"

    if (version == "2024" or version == "2") and search_engine == "brave":
        with open(get_data_search_dir(version, data_type, search_date, search_engine), "r") as f:
            return json.load(f)
    else:
        raise Exception()

def save_data_search(data, data_type, search_date, version="2024", search_engine="brave"):
    assert data_type in type_list, f"data_type需要从{type_list}中选择！"

    if (version == "2024" or version == "2") and search_engine == "brave":
        with open(get_data_search_dir(version, data_type, search_date, search_engine), "w") as f:
            json.dump(data, f, indent=4)
    else:
        raise Exception()
    
# def save_test_search(data, version="2024", search_engine="brave"):

#     if version == "2024" and search_engine == "brave":
#         with open(f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS-2024/training/test_brave_search.json", "w") as f:
#             json.dump(data, f, indent=4)
#     else:
#         raise Exception()
    
# def load_test_search(version="2024", search_engine="brave"):

#     if version == "2024" and search_engine == "brave":
#         with open(f"/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS-2024/training/test_brave_search.json", "r") as f:
#             return json.load(f)
#     else:
#         raise Exception()

# def load_test(version="2024"):
#     """
#     版本选择："2024" or "original"
#     """
    
#     if version == "2024":
#         with open("/home/hanlv/workspace/data/machine_learning/dataset/research/misinformation_dataset/COVMIS-2024/training/test.json", "r") as f:
#             return json.load(f)
#     else:
#         raise Exception(f"version需要从{version_list}中选择！")