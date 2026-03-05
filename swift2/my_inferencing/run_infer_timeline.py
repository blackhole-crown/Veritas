ckpt_list = [
    "/home/hanlv/workspace/code/research/infodemic/misinformation/CEMD/swift2/output/covmis/Llama-3-8B-Instruct/with_llama3_info/brave/data1-split=8:2-ratio=1.0/dora-r=8/lr=1e-4-20240626-06:24:36/checkpoint-609",
]
import os
import subprocess
os.environ['CUDA_VISIBLE_DEVICES'] = '2'
root_dir = '/home/hanlv/workspace/code/research/infodemic/misinformation/CEMD/swift2/my_data/covmis/with_llama3_info/brave/train_valid_split/8:2/timeline_data1'
data_type = "test" # test, valid
for file in os.listdir(root_dir):
    data_dir = os.path.join(root_dir, file)
    
    for ckpt in ckpt_list:
        subprocess.run(["python", "infer_tuned.py", 
                        "--ckpt_dir", ckpt,
                        "--data_dir", data_dir,
                        "--data_type", data_type,
        ])

