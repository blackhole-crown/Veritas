#!/bin/bash

# 激活 conda 环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate xinference

echo "🚀 Launching model: gte-Qwen2"
echo "📁 Model path: /data/zhouzehui/models/gte_Qwen2-1_5B-instruct"

# 启动模型
xinference launch --model-name gte-Qwen2 --model-type embedding --replica 1 --n-gpu auto --gpu-idx 0 --model-path /data/zhouzehui/models/gte_Qwen2-1_5B-instruct

echo "✅ Model launch command executed"


