#!/bin/bash

# 设置基础路径（从脚本位置计算）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"  # 上两级目录到 addon_v1_qwen3_api
RUN_MODEL_DIR="$BASE_DIR/run_model"

# 动态生成日期和时间
TODAY=$(date +"%m%d")
CURRENT_TIME=$(date +"%H%M%S")
FULL_TIMESTAMP=$(date +"%m%d_%H%M%S")

echo "Current timestamp: $FULL_TIMESTAMP"

# 设置日志目录
LOG_BASE_DIR="$RUN_MODEL_DIR/nohup/Xinference"
LOG_DIR="$LOG_BASE_DIR/$TODAY/$CURRENT_TIME"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "🚀 Starting Xinference Service with Model"
echo "=========================================="
echo "📅 Date: $TODAY"
echo "⏰ Time: $CURRENT_TIME"
echo "📁 Base Directory: $BASE_DIR"
echo "📁 Run Model Directory: $RUN_MODEL_DIR"
echo "📁 Log directory: $LOG_DIR"
echo "⏰ Start time: $(date)"
echo "🎯 Port: 9997"

# 设置脚本路径
MODEL_SCRIPT="$RUN_MODEL_DIR/Gte-Qwen-2B/xinference.sh"

# 检查脚本是否存在
if [ ! -f "$MODEL_SCRIPT" ]; then
    echo "❌ Error: Model script not found: $MODEL_SCRIPT"
    exit 1
fi

# 给执行权限
chmod +x "$MODEL_SCRIPT"

# 第一步：启动 Xinference 服务
echo "🔧 Step 1: Starting Xinference service..."

# 创建 Xinference 服务启动脚本
cat > "$LOG_DIR/start_xinference_service.sh" << 'EOF'
#!/bin/bash
# 激活 conda 环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate xinference

echo "🚀 Starting Xinference service on port 9997..."
echo "📁 Working directory: $(pwd)"

# 启动 Xinference 服务
xinference-local --host 0.0.0.0 --port 9997
EOF

chmod +x "$LOG_DIR/start_xinference_service.sh"

# 在后台启动 Xinference 服务
cd "$BASE_DIR"
nohup bash "$LOG_DIR/start_xinference_service.sh" > "$LOG_DIR/xinference_service.log" 2>&1 &

XINFERENCE_PID=$!
echo $XINFERENCE_PID > "$LOG_DIR/xinference_pid.txt"
echo "✅ Xinference service started with PID: $XINFERENCE_PID"

# 等待服务启动
echo "⏳ Waiting for Xinference service to start..."
for i in {1..30}; do
    if lsof -ti:9997 > /dev/null; then
        echo "✅ Xinference service is ready on port 9997"
        break
    fi
    echo "⏳ Waiting for Xinference service to start... ($i/30)"
    sleep 2
done

if ! lsof -ti:9997 > /dev/null; then
    echo "❌ Xinference service failed to start within 60 seconds"
    echo "📋 Check the service log: $LOG_DIR/xinference_service.log"
    tail -20 "$LOG_DIR/xinference_service.log"
    exit 1
fi

# 第二步：等待服务完全初始化
echo "⏳ Step 2: Waiting for Xinference to fully initialize..."
sleep 10

# 第三步：启动模型部署
echo "🔧 Step 3: Starting model deployment..."

# 创建模型部署包装脚本
cat > "$LOG_DIR/model_deploy_wrapper.sh" << 'EOF'
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
EOF

chmod +x "$LOG_DIR/model_deploy_wrapper.sh"

# 执行模型部署
cd "$RUN_MODEL_DIR/Gte-Qwen-2B"
nohup bash "$LOG_DIR/model_deploy_wrapper.sh" > "$LOG_DIR/model_deployment.log" 2>&1 &

MODEL_PID=$!
echo $MODEL_PID > "$LOG_DIR/model_pid.txt"

# 记录启动信息
echo "$(date)" > "$LOG_DIR/start_time.txt"
echo "$FULL_TIMESTAMP" > "$LOG_DIR/timestamp.txt"

echo "=========================================="
echo "🎯 Xinference Service Started Successfully!"
echo "=========================================="
echo "📊 Process IDs:"
echo "   - Xinference Service: $XINFERENCE_PID"
echo "   - Model Deployment: $MODEL_PID"
echo ""
echo "📝 Log Files:"
echo "   - Xinference Service: $LOG_DIR/xinference_service.log"
echo "   - Model Deployment: $LOG_DIR/model_deployment.log"
echo "🆔 PID Files:"
echo "   - Xinference: $LOG_DIR/xinference_pid.txt"
echo "   - Model: $LOG_DIR/model_pid.txt"
echo "⏰ Timestamp: $FULL_TIMESTAMP"
echo "🌐 Service URL: http://0.0.0.0:9997"

# 验证启动 - 等待更长时间并检查模型是否注册
echo ""
echo "🔍 Service status (waiting for model registration)..."
sleep 20

check_process_status() {
    local pid=$1
    local service_name=$2
    if ps -p $pid > /dev/null; then
        echo "✅ $service_name process is running (PID: $pid)"
        return 0
    else
        echo "❌ $service_name process is not running (PID: $pid)"
        return 1
    fi
}

check_process_status $XINFERENCE_PID "Xinference Service"
check_process_status $MODEL_PID "Model Deployment"

# 检查模型是否在服务中注册
echo ""
echo "🔍 Checking model registration..."
sleep 5

# 检查模型列表
if curl -s http://0.0.0.0:9997/v1/models > /dev/null 2>&1; then
    echo "✅ Xinference API is responding"
    MODEL_LIST=$(curl -s http://0.0.0.0:9997/v1/models 2>/dev/null)
    if echo "$MODEL_LIST" | grep -q "gte-Qwen2"; then
        echo "✅ Model gte-Qwen2 is registered in Xinference"
    else
        echo "❌ Model gte-Qwen2 is not found in Xinference"
        echo "Available models:"
        echo "$MODEL_LIST" | python -m json.tool 2>/dev/null || echo "$MODEL_LIST"
    fi
else
    echo "❌ Cannot connect to Xinference API"
fi

# 检查错误日志
echo ""
echo "📋 Recent logs:"
if [ -f "$LOG_DIR/model_deployment.log" ]; then
    echo "Model deployment log (last 5 lines):"
    tail -5 "$LOG_DIR/model_deployment.log"
fi

if [ -f "$LOG_DIR/xinference_service.log" ]; then
    echo "Xinference service log (last 5 lines):"
    tail -5 "$LOG_DIR/xinference_service.log"
fi

echo ""
echo "🔍 Useful commands:"
echo "   tail -f $LOG_DIR/model_deployment.log"
echo "   tail -f $LOG_DIR/xinference_service.log"
echo "   curl -s http://0.0.0.0:9997/v1/models | python -m json.tool"
echo "   lsof -ti:9997"
echo "   kill $XINFERENCE_PID $MODEL_PID"

# 显示目录结构
echo ""
echo "📁 Current log directory structure:"
find "$LOG_BASE_DIR/$TODAY" -type d -name "*" | sort