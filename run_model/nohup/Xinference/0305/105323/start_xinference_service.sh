#!/bin/bash
# 激活 conda 环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate xinference

echo "🚀 Starting Xinference service on port 9997..."
echo "📁 Working directory: $(pwd)"

# 启动 Xinference 服务
xinference-local --host 0.0.0.0 --port 9997
