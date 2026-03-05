import time
# time.sleep(3600*2.8) # 让程序等待x小时

ckpt_list = [

]
import os
import subprocess
import run_infer_base
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

files = []

# 获取当前目录下的所有文件
for base_dir in [
    '/home/hanlv/workspace/code/research/infodemic/LLM/swift/examples/pytorch/llm/output/covmis_wsc2/Llama-3-8B-Instruct/with_llama3_info/brave/data1-split=8:2-ratio=1.0',
]:
    files.extend([os.path.join(base_dir, file) for file in os.listdir(base_dir)])

# 遍历文件列表，输出文件名
for path in files:
    
# for path in [
#     "/home/hanlv/workspace/code/research/infodemic/LLM/swift/examples/pytorch/llm/output/covmis/Llama-3-8B-Instruct/with_llama3_info/brave/data1-split=8:2-ratio=1.0/dora-r=2",
#     "/home/hanlv/workspace/code/research/infodemic/LLM/swift/examples/pytorch/llm/output/covmis/Llama-3-8B-Instruct/with_llama3_info/brave/data1-split=8:2-ratio=1.0/dora-r=4",
#     "/home/hanlv/workspace/code/research/infodemic/LLM/swift/examples/pytorch/llm/output/covmis/Llama-3-8B-Instruct/with_llama3_info/brave/data1-split=8:2-ratio=1.0/dora-r=16",
#     "/home/hanlv/workspace/code/research/infodemic/LLM/swift/examples/pytorch/llm/output/covmis/Llama-3-8B-Instruct/with_llama3_info/brave/data1-split=8:2-ratio=1.0/dora-r=32",

# ]:

    data_dir = ""
    # data_dir = "/home/hanlv/workspace/code/research/infodemic/LLM/swift/examples/pytorch/llm/my_data/liar2/with_llama3_info/brave/train_valid_split/8:1:1/test_data1.jsonl"

    data_type = "test" # test, valid

    # 要运行的Python文件的路径
    if len(ckpt_list) == 0 and len(path) == 0:
        raise Exception()
    # if len(ckpt_list) > 0 and len(path) > 0:
    #     raise Exception()

    if len(path) > 0:
        for file in os.listdir(path):
            ckpts = run_infer_base.get_ckpts(os.path.join(path, file))
            if len(ckpts) == 0:
                continue
            ckpt_list.append(ckpts[0])

    # 使用subprocess运行Python文件
    for ckpt in ckpt_list:
        subprocess.run(["python", "infer_tuned.py", 
                        "--ckpt_dir", ckpt,
                        "--data_dir", data_dir,
                        "--data_type", data_type,
    ])

