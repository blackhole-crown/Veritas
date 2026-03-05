#!/bin/bash
# 设置环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate xinference

# 环境信息
echo "=== Deployment Environment ==="
echo "Time: $(date)"
echo "Conda Environment: $CONDA_DEFAULT_ENV"
echo "Python: $(which python)"
echo "Xinference: $(which xinference)"
echo "Working Directory: $(pwd)"
echo "==============================="

# 执行模型部署
echo "🚀 Launching model: gte-Qwen2"
xinference launch --model-name gte-Qwen2 --model-type embedding --replica 1 --n-gpu auto --gpu-idx 0 --model-path /data/zhouzehui/models/gte_Qwen2-1_5B-instruct

echo "✅ Model deployment command completed"
