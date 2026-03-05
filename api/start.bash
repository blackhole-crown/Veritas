#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 获取项目根目录（脚本所在目录的父目录，因为脚本在 api 子目录中）
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "🚀 Starting All Services"
echo "=========================================="
echo "📁 Script Directory: $SCRIPT_DIR"
echo "📁 Project Root: $PROJECT_ROOT"

# 切换到项目根目录（因为 app.py 和 celery_app.py 都在根目录）
cd "$PROJECT_ROOT" || { echo "❌ Failed to cd into $PROJECT_ROOT"; exit 1; }
echo "✅ Working directory: $(pwd)"

# 动态生成日期和时间
TODAY=$(date +"%m%d")
CURRENT_TIME=$(date +"%H%M%S")
FULL_TIMESTAMP=$(date +"%m%d_%H%M%S")

echo "Current timestamp: $FULL_TIMESTAMP"

# 设置日志目录 - 在 api 目录下
LOG_BASE_DIR="$SCRIPT_DIR/logs"
LOG_DIR="$LOG_BASE_DIR/$TODAY/$CURRENT_TIME"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo "📁 Log directory: $LOG_DIR"
echo "⏰ Start time: $(date)"

# 激活 conda 环境
echo "🔧 Activating conda environment..."
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    echo "⚠️  Could not find conda.sh, trying to use conda from PATH"
fi

if conda activate addon_v1 2>/dev/null; then
    echo "✅ Conda environment activated: addon_v1"
else
    echo "❌ Failed to activate conda environment: addon_v1"
    echo "⚠️  Trying to continue without conda environment..."
fi

# 检查必要文件是否存在（在项目根目录检查）
echo "🔍 Checking required files in $PROJECT_ROOT..."

if [ ! -f "$PROJECT_ROOT/celery_app.py" ]; then
    echo "❌ Error: celery_app.py not found in $PROJECT_ROOT"
    echo "📁 Project root files:"
    ls -la "$PROJECT_ROOT" | grep -E "celery_app|app"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/app.py" ]; then
    echo "❌ Error: app.py not found in $PROJECT_ROOT"
    echo "📁 Project root files:"
    ls -la "$PROJECT_ROOT" | grep -E "celery_app|app"
    exit 1
fi

echo "✅ Found celery_app.py and app.py in project root"

# 设置 Celery 应用
CELERY_APP="celery_app"
echo "✅ Using Celery app: $CELERY_APP"

# 创建 Celery 结果目录
echo "📁 创建 Celery 结果目录..."
CELERY_RESULT_DIR="$LOG_DIR/celery_results"
mkdir -p "$CELERY_RESULT_DIR"
echo "✅ Celery 结果目录: $CELERY_RESULT_DIR"

# 清理旧的结果文件（可选）
echo "🧹 清理旧的结果文件..."
python -c "
import os, time, glob
result_dir = '$CELERY_RESULT_DIR'
if os.path.exists(result_dir):
    cutoff = time.time() - (7 * 24 * 3600)  # 7天前
    for file in glob.glob(os.path.join(result_dir, '*')):
        if os.path.isfile(file) and os.path.getmtime(file) < cutoff:
            os.remove(file)
            print(f'删除旧文件: {os.path.basename(file)}')
" 2>/dev/null || echo "⚠️  Python script execution skipped (non-critical)"

# 启动 Celery Worker（在项目根目录）
echo "🎯 Starting Celery Worker..."
nohup celery -A $CELERY_APP worker --loglevel=info --concurrency=1 > "$LOG_DIR/celery_nohup.txt" 2> "$LOG_DIR/celery_error.txt" &
CELERY_PID=$!
echo $CELERY_PID > "$LOG_DIR/celery_pid.txt"
echo "✅ Celery Worker started with PID: $CELERY_PID (in directory: $PROJECT_ROOT)"

# 等待 Celery 启动
sleep 5

# 2. 启动 Flask 应用（在项目根目录）
echo "🎯 Starting Flask Application..."
nohup python app.py > "$LOG_DIR/flask_nohup.txt" 2> "$LOG_DIR/flask_error.txt" &

FLASK_PID=$!
echo $FLASK_PID > "$LOG_DIR/flask_pid.txt"
echo "✅ Flask Application started with PID: $FLASK_PID (in directory: $PROJECT_ROOT)"

# 等待 Flask 启动
sleep 3

# 3. 启动 Flower 监控（在项目根目录）
echo "🎯 Starting Flower Monitor..."
nohup celery -A $CELERY_APP flower --port=5556 > "$LOG_DIR/flower_nohup.txt" 2> "$LOG_DIR/flower_error.txt" &

FLOWER_PID=$!
echo $FLOWER_PID > "$LOG_DIR/flower_pid.txt"
echo "✅ Flower Monitor started with PID: $FLOWER_PID (in directory: $PROJECT_ROOT)"

# 记录启动信息
echo "$(date)" > "$LOG_DIR/start_time.txt"
echo "$FULL_TIMESTAMP" > "$LOG_DIR/timestamp.txt"

echo "=========================================="
echo "🎯 All Services Started Successfully!"
echo "=========================================="
echo "📊 Process IDs:"
echo "   - Celery Worker: $CELERY_PID"
echo "   - Flask App: $FLASK_PID"
echo "   - Flower Monitor: $FLOWER_PID"
echo ""
echo "📁 Working Directories:"
echo "   - All services: $PROJECT_ROOT"
echo ""
echo "📝 Log Files:"
echo "   - Celery: $LOG_DIR/celery_nohup.txt"
echo "   - Flask: $LOG_DIR/flask_nohup.txt"
echo "   - Flower: $LOG_DIR/flower_nohup.txt"
echo "❌ Error Files:"
echo "   - Celery: $LOG_DIR/celery_error.txt"
echo "   - Flask: $LOG_DIR/flask_error.txt"
echo "   - Flower: $LOG_DIR/flower_error.txt"
echo "🆔 PID Files:"
echo "   - Celery: $LOG_DIR/celery_pid.txt"
echo "   - Flask: $LOG_DIR/flask_pid.txt"
echo "   - Flower: $LOG_DIR/flower_pid.txt"
echo "⏰ Timestamp: $FULL_TIMESTAMP"
echo ""
echo "🌐 Service URLs:"
echo "   - Flask App: http://0.0.0.0:5000 (or your configured port)"
echo "   - Flower Monitor: http://0.0.0.0:5556"

# 验证启动
sleep 10
echo ""
echo "🔍 Service Status:"

check_process_status() {
    local pid=$1
    local service_name=$2
    if ps -p $pid > /dev/null 2>&1; then
        echo "✅ $service_name is running properly!"
        return 0
    else
        echo "❌ $service_name may have failed to start."
        return 1
    fi
}

check_process_status $CELERY_PID "Celery Worker"
check_process_status $FLASK_PID "Flask Application" 
check_process_status $FLOWER_PID "Flower Monitor"

# 检查错误日志
echo ""
echo "🔍 Checking error logs if any services failed..."

if ! ps -p $CELERY_PID > /dev/null 2>&1; then
    echo "📋 Celery error log:"
    tail -10 "$LOG_DIR/celery_error.txt" 2>/dev/null || echo "No celery error log found"
fi

if ! ps -p $FLASK_PID > /dev/null 2>&1; then
    echo "📋 Flask error log:"
    tail -10 "$LOG_DIR/flask_error.txt" 2>/dev/null || echo "No flask error log found"
fi

if ! ps -p $FLOWER_PID > /dev/null 2>&1; then
    echo "📋 Flower error log:"
    tail -10 "$LOG_DIR/flower_error.txt" 2>/dev/null || echo "No flower error log found"
fi

# 显示最近的日志内容
echo ""
echo "🔍 Recent log entries:"
echo "📋 Last 5 lines of Celery log:"
tail -5 "$LOG_DIR/celery_nohup.txt" 2>/dev/null || echo "No celery log found"
echo ""
echo "📋 Last 5 lines of Flask log:"
tail -5 "$LOG_DIR/flask_nohup.txt" 2>/dev/null || echo "No flask log found"

echo ""
echo "🔍 Useful commands:"
echo "   tail -f $LOG_DIR/celery_nohup.txt"
echo "   tail -f $LOG_DIR/flask_nohup.txt"
echo "   tail -f $LOG_DIR/flower_nohup.txt"
echo "   kill $CELERY_PID $FLASK_PID $FLOWER_PID"

# 显示日志目录结构
echo ""
echo "📁 Current log directory structure:"
if [ -d "$LOG_BASE_DIR/$TODAY" ]; then
    find "$LOG_BASE_DIR/$TODAY" -type d -name "*" | sort
    echo ""
    echo "📁 Log files in current session:"
    ls -la "$LOG_DIR"
else
    echo "No log directory found for today"
fi