#!/bin/bash

# 设置基础路径（从脚本位置计算）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"  # 上两级目录到 addon_v1_qwen3_api
RUN_MODEL_DIR="$BASE_DIR/run_model"
LOG_BASE_DIR="$RUN_MODEL_DIR/nohup/Xinference"

# 动态生成日期和时间
TODAY=$(date +"%m%d")
CURRENT_TIME=$(date +"%H%M%S")

# 找到最新的日志目录（应该是刚刚创建的）
LATEST_DIR=$(find "$LOG_BASE_DIR/$TODAY" -type d -name "$CURRENT_TIME" 2>/dev/null | head -1)

if [ -z "$LATEST_DIR" ]; then
    # 如果找不到，可能是时间戳稍有差异，找最新的目录
    LATEST_DIR=$(find "$LOG_BASE_DIR/$TODAY" -type d | sort | tail -1)
    echo "⚠️  Using latest log directory: $LATEST_DIR"
fi

if [ -z "$LATEST_DIR" ]; then
    echo "❌ Error: Cannot find log directory"
    echo "📁 Available directories in $LOG_BASE_DIR/$TODAY:"
    find "$LOG_BASE_DIR/$TODAY" -type d 2>/dev/null || echo "No directories found"
    exit 1
fi

echo "🚀 Starting Xinference service on port 9997..."
echo "📁 Base Directory: $BASE_DIR"
echo "📁 Log directory: $LATEST_DIR"

# 激活 conda 环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate xinference

# 启动 Xinference 服务
echo "🎯 Starting xinference-local..."
cd "$BASE_DIR"  # 切换到项目根目录
nohup xinference-local --host 0.0.0.0 --port 9997 > "$LATEST_DIR/xinference_nohup.txt" 2> "$LATEST_DIR/xinference_error.txt" &

XINFERENCE_PID=$!
echo $XINFERENCE_PID > "$LATEST_DIR/xinference_pid.txt"

echo "✅ Xinference service started with PID: $XINFERENCE_PID"
echo "⏳ Waiting for service to initialize..."

# 等待服务启动
for i in {1..30}; do
    if lsof -ti:9997 > /dev/null; then
        echo "✅ Xinference service is ready on port 9997"
        echo "📋 Service logs: $LATEST_DIR/xinference_nohup.txt"
        break
    fi
    echo "⏳ Waiting for Xinference service to start... ($i/30)"
    sleep 2
done

if ! lsof -ti:9997 > /dev/null; then
    echo "❌ Xinference service failed to start within 60 seconds"
    echo "📋 Check the error log: $LATEST_DIR/xinference_error.txt"
    tail -20 "$LATEST_DIR/xinference_error.txt"
    exit 1
fi