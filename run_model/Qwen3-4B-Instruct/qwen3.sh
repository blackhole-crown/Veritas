
# 激活 conda 环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate swift

CUDA_VISIBLE_DEVICES=0 \
swift deploy \
--model_type qwen3_nothinking \
--model /data/zhouzehui/models/Qwen/Qwen3-4B-Instruct-2507 \
--infer_backend vllm \
--gpu_memory_utilization 0.35 \
--temperature 0 \
--tensor_parallel_size 1 \
--host 127.0.0.1 \
--port 8006 \
--vllm_max_num_seqs 4 \
--max_model_len 32768
