import os

def get_ckpts(file):
    """
    file: "/home/hanlv/workspace/code/research/infodemic/LLM/swift/examples/pytorch/llm/output/liar2/Llama-3-8B-Instruct/with_llama3_info/brave/data1.6-split=8:1:1-ratio=1.0/dora-r=8/lr=1.1e-4-20240822-00:09:55"
    """
    if not os.path.exists(os.path.join(file, 'images')):
        print(f'未训练结束: {file}\n')
        return []
    ckpts = []
    for s in os.listdir(file):
        if s.startswith('checkpoint-'):
            ckpts.append(os.path.join(file, s))
    
    if len(ckpts) > 1:
        raise Exception(f"Too many checkpoints: {ckpts} in path: {file}")
    # elif len(ckpts) == 0:
    #     raise Exception(f"No checkpoint in path: {file}")
    return ckpts