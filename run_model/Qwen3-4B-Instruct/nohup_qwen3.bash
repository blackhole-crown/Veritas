#!/bin/bash

# 设置基础路径（相对于脚本位置）
BASE_DIR="../../.."
SCRIPT_DIR="./run_model/Qwen3-4B-Instruct"
SCRIPT_PATH="$SCRIPT_DIR/qwen3.sh"

# 动态生成日期和时间
TODAY=$(date +"%m%d")
CURRENT_TIME=$(date +"%H%M%S")  # 时分秒，如 235131
FULL_TIMESTAMP=$(date +"%m%d_%H%M%S")  # 完整时间戳，如 1106_235131

echo "Current timestamp: $FULL_TIMESTAMP"

# 设置日志目录 - 在日期目录下创建时间子目录
LOG_BASE_DIR="./run_model/nohup/Qwen3_4B-Instruct"
LOG_DIR="$LOG_BASE_DIR/$TODAY/$CURRENT_TIME"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "🚀 Starting Qwen3-4B-Instruct Service"
echo "=========================================="
echo "📅 Date: $TODAY"
echo "⏰ Time: $CURRENT_TIME"
echo "📁 Script: $SCRIPT_PATH"
echo "📁 Log directory: $LOG_DIR"
echo "⏰ Start time: $(date)"

# 检查脚本是否存在
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: Script not found: $SCRIPT_PATH"
    exit 1
fi

# 给执行权限（如果需要）
chmod +x "$SCRIPT_PATH"

# 激活 conda 环境
echo "🔧 Activating conda environment: swift3"
source ~/miniconda3/etc/profile.d/conda.sh
if conda activate swift3; then
    echo "✅ Conda environment activated: swift3"
else
    echo "❌ Failed to activate conda environment: swift3"
    exit 1
fi

# 启动服务
echo "🎯 Starting Qwen3 service..."
nohup bash "$SCRIPT_PATH" > "$LOG_DIR/nohup.txt" 2> "$LOG_DIR/error.txt" &

# 获取进程 ID
PID=$!
echo $PID > "$LOG_DIR/pid.txt"
echo "$(date)" > "$LOG_DIR/start_time.txt"
echo "$FULL_TIMESTAMP" > "$LOG_DIR/timestamp.txt"

echo "=========================================="
echo "🎯 Service Started Successfully!"
echo "=========================================="
echo "📊 PID: $PID"
echo "📝 Log file: $LOG_DIR/nohup.txt"
echo "❌ Error file: $LOG_DIR/error.txt"
echo "🆔 PID file: $LOG_DIR/pid.txt"
echo "⏰ Timestamp: $FULL_TIMESTAMP"

# 验证启动
sleep 3
if ps -p $PID > /dev/null; then
    echo "✅ Service is running properly!"
    echo ""
    echo "🔍 Useful commands:"
    echo "   tail -f $LOG_DIR/nohup.txt"
    echo "   tail -f $LOG_DIR/error.txt"
    echo "   kill $PID"
else
    echo "❌ Service may have failed to start."
    echo "Checking error log..."
    tail -10 "$LOG_DIR/error.txt"
fi

# 显示目录结构
echo ""
echo "📁 Current log directory structure:"
find "$LOG_BASE_DIR/$TODAY" -type d -name "*" | sort