import subprocess
import time

with_or_without_info = 'without_info'   # 'without_info', 'with_llama3_info', 'with_info'


# from create_prompt_llm import run_update_train_search_llm
for _ in range(10):
    subprocess.run(["python", "infer_no_rag_no_tune.py", 
                    "--with_or_without_info", with_or_without_info,
    ])
    time.sleep(3) # 让程序等待1小时

