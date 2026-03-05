import json

type_list = ["train", "valid", "test"]

def get_data_dir(data_type):
    return f"/home/hanlv/workspace/data/machine_learning/dataset/research/fake_news_dataset/liar2/liar2/{data_type}.json"

def get_data_llm_dir(data_type, search_engine="brave"):
    return f"/home/hanlv/workspace/data/machine_learning/dataset/research/fake_news_dataset/liar2/liar2/{data_type}_{search_engine}_search_llm.json"

def get_data_search_dir(data_type, search_engine="brave"):
    return f"/home/hanlv/workspace/data/machine_learning/dataset/research/fake_news_dataset/liar2/liar2/{data_type}_{search_engine}_search.json"


def load_data(data_type):
    """
    type: train or valid or test
    """

    assert data_type in type_list, f"data_type需要从{type_list}中选择！"

    with open(get_data_dir(data_type), "r") as f:
        return json.load(f)


def save_data(data, data_type):

    assert data_type in type_list, f"data_type需要从{type_list}中选择！"

    with open(get_data_dir(data_type), "w") as f:
        json.dump(data, f, indent=4)

def load_data_llm(data_type, search_engine="brave"):

    assert data_type in type_list, f"data_type需要从{type_list}中选择！"

    if search_engine == "brave":
        with open(get_data_llm_dir(data_type, search_engine), "r") as f:
            return json.load(f)
    else:
        raise Exception()

def save_data_llm(data, data_type, search_engine="brave"):

    assert data_type in type_list, f"data_type需要从{type_list}中选择！"

    if search_engine == "brave":
        with open(get_data_llm_dir(data_type, search_engine), "w") as f:
            json.dump(data, f, indent=4)
    else:
        raise Exception()

def load_data_search(data_type, search_engine="brave"):

    assert data_type in type_list, f"data_type需要从{type_list}中选择！"
    if search_engine == "brave":
        with open(get_data_search_dir(data_type, search_engine), "r") as f:
            return json.load(f)
    else:
        raise Exception()

def save_data_search(data, data_type, search_engine="brave"):

    assert data_type in type_list, f"data_type需要从{type_list}中选择！"
    if search_engine == "brave":
        with open(get_data_search_dir(data_type, search_engine), "w") as f:
            json.dump(data, f, indent=4)
    else:
        raise Exception()