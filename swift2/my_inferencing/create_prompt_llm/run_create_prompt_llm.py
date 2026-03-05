import subprocess
import time



# from create_prompt_llm import run_update_train_search_llm
for data_type in ["train", "valid", "test"]:
    subprocess.run(["python", "create_prompt_llm.py", 
                    "--data_type", data_type,
    ])
    time.sleep(3) # 让程序等待1小时

