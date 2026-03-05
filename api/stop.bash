#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 获取项目根目录（脚本所在目录的父目录，因为脚本在 api 子目录中）
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
# 日志基础目录在脚本目录下的 logs
LOG_BASE_DIR="$SCRIPT_DIR/logs"

echo "=========================================="
echo "🛑 Stopping All Services"
echo "=========================================="
echo "📁 Script Directory: $SCRIPT_DIR"
echo "📁 Project Root: $PROJECT_ROOT"
echo "📁 Log Base Directory: $LOG_BASE_DIR"

# 切换到项目根目录
cd "$PROJECT_ROOT" || { echo "❌ Failed to cd into $PROJECT_ROOT"; exit 1; }

# 方法1：通过PID文件停止
stop_by_pid_file() {
    echo "🔍 Looking for PID files in: $LOG_BASE_DIR"
    
    # 查找最新的包含 PID 文件的目录（排除 _stopped 的目录）
    local LATEST_DIR=$(find "$LOG_BASE_DIR" -name "celery_pid.txt" -type f 2>/dev/null | grep -v "_stopped" | xargs dirname | sort | tail -1)
    
    if [ -z "$LATEST_DIR" ]; then
        echo "ℹ️  No active PID file found, trying other methods..."
        return 1
    fi

    CELERY_PID_FILE="$LATEST_DIR/celery_pid.txt"
    FLASK_PID_FILE="$LATEST_DIR/flask_pid.txt"
    FLOWER_PID_FILE="$LATEST_DIR/flower_pid.txt"
    
    echo "📁 Found service directory: $LATEST_DIR"
    
    # 停止 Celery Worker 进程
    if [ -f "$CELERY_PID_FILE" ]; then
        CELERY_PID=$(cat "$CELERY_PID_FILE")
        echo "🎯 Found Celery PID: $CELERY_PID"
        
        if ps -p $CELERY_PID > /dev/null 2>&1; then
            echo "⏳ Stopping Celery process: $CELERY_PID"
            # 尝试停止整个进程组
            PGID=$(ps -o pgid= $CELERY_PID 2>/dev/null | grep -o '[0-9]*')
            if [ ! -z "$PGID" ]; then
                kill -- -$PGID 2>/dev/null
            else
                kill $CELERY_PID 2>/dev/null
            fi
            sleep 2
            
            if ps -p $CELERY_PID > /dev/null 2>&1; then
                echo "⚠️  Celery process still running, forcing kill..."
                kill -9 $CELERY_PID 2>/dev/null
            fi
            
            echo "✅ Celery process stopped"
        else
            echo "ℹ️  Celery process not running (PID: $CELERY_PID)"
        fi
    fi
    
    # 停止 Flask 应用进程
    if [ -f "$FLASK_PID_FILE" ]; then
        FLASK_PID=$(cat "$FLASK_PID_FILE")
        echo "🎯 Found Flask PID: $FLASK_PID"
        
        if ps -p $FLASK_PID > /dev/null 2>&1; then
            echo "⏳ Stopping Flask process: $FLASK_PID"
            # 先终止子进程，再终止父进程
            CHILD_PROCESSES=$(ps -ef | awk -v pid="$FLASK_PID" '$3 == pid {print $2}')
            for CHILD_PID in $CHILD_PROCESSES; do
                echo "⏳ Stopping child process: $CHILD_PID"
                kill $CHILD_PID 2>/dev/null
                sleep 1
                if ps -p $CHILD_PID > /dev/null 2>&1; then
                    kill -9 $CHILD_PID 2>/dev/null
                fi
            done
            
            kill $FLASK_PID 2>/dev/null
            sleep 2
            if ps -p $FLASK_PID > /dev/null 2>&1; then
                echo "⚠️  Flask process still running, forcing kill..."
                kill -9 $FLASK_PID 2>/dev/null
            fi
            
            echo "✅ Flask process stopped"
        else
            echo "ℹ️  Flask process not running (PID: $FLASK_PID)"
        fi
    fi
    
    # 停止 Flower 监控进程
    if [ -f "$FLOWER_PID_FILE" ]; then
        FLOWER_PID=$(cat "$FLOWER_PID_FILE")
        echo "🎯 Found Flower PID: $FLOWER_PID"
        
        if ps -p $FLOWER_PID > /dev/null 2>&1; then
            echo "⏳ Stopping Flower process: $FLOWER_PID"
            PGID=$(ps -o pgid= $FLOWER_PID 2>/dev/null | grep -o '[0-9]*')
            if [ ! -z "$PGID" ]; then
                kill -- -$PGID 2>/dev/null
            else
                kill $FLOWER_PID 2>/dev/null
            fi
            sleep 2
            
            if ps -p $FLOWER_PID > /dev/null 2>&1; then
                echo "⚠️  Flower process still running, forcing kill..."
                kill -9 $FLOWER_PID 2>/dev/null
            fi
            
            echo "✅ Flower process stopped"
        else
            echo "ℹ️  Flower process not running (PID: $FLOWER_PID)"
        fi
    fi
    
    # 重命名目录表示已停止
    STOPPED_DIR="${LATEST_DIR}_stopped_$(date +%H%M%S)"
    mv "$LATEST_DIR" "$STOPPED_DIR" 2>/dev/null && echo "📁 Moved to: $STOPPED_DIR"
    
    return 0
}

# 方法2：通过端口停止
stop_by_port() {
    echo "🔍 Checking processes by port..."
    
    # 停止 Flower 监控端口
    FLOWER_PORTS=$(lsof -ti:5556 2>/dev/null)
    if [ ! -z "$FLOWER_PORTS" ]; then
        echo "🎯 Found processes on port 5556: $FLOWER_PORTS"
        for PID in $FLOWER_PORTS; do
            echo "⏳ Stopping process on port 5556: $PID"
            kill -9 $PID 2>/dev/null
            echo "✅ Stopped process: $PID"
        done
    fi
    
    # 停止 Flask 应用端口（假设默认5000）
    FLASK_PORTS=$(lsof -ti:5000 2>/dev/null)
    if [ ! -z "$FLASK_PORTS" ]; then
        echo "🎯 Found processes on port 5000: $FLASK_PORTS"
        for PID in $FLASK_PORTS; do
            echo "⏳ Stopping process on port 5000: $PID"
            kill -9 $PID 2>/dev/null
            echo "✅ Stopped process: $PID"
        done
    fi
}

# 方法3：通过进程名停止
stop_by_process_name() {
    echo "🔍 Checking for service processes in project: $PROJECT_ROOT"
    
    # 查找在项目目录下运行的 Celery 相关进程
    CELERY_PROCESSES=$(ps aux | grep -E "celery.*worker|celery.*flower" | grep -v grep | grep "$PROJECT_ROOT" | awk '{print $2}')
    if [ ! -z "$CELERY_PROCESSES" ]; then
        for PID in $CELERY_PROCESSES; do
            echo "🎯 Found Celery process: PID=$PID"
            PGID=$(ps -o pgid= $PID 2>/dev/null | grep -o '[0-9]*')
            if [ ! -z "$PGID" ]; then
                kill -- -$PGID 2>/dev/null
            else
                kill $PID 2>/dev/null
            fi
            sleep 1
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID 2>/dev/null
                echo "✅ Forcibly stopped Celery process: $PID"
            else
                echo "✅ Stopped Celery process: $PID"
            fi
        done
    fi
    
    # 查找在项目目录下运行的 Flask 相关进程
    FLASK_PROCESSES=$(ps aux | grep -E "python.*app\.py|python.*api\.py" | grep -v grep | grep "$PROJECT_ROOT" | awk '{print $2}')
    if [ ! -z "$FLASK_PROCESSES" ]; then
        for PID in $FLASK_PROCESSES; do
            echo "🎯 Found Flask process: PID=$PID"
            # 先终止子进程
            CHILD_PROCESSES=$(ps -ef | awk -v pid="$PID" '$3 == pid {print $2}')
            for CHILD_PID in $CHILD_PROCESSES; do
                kill $CHILD_PID 2>/dev/null
                sleep 1
                if ps -p $CHILD_PID > /dev/null 2>&1; then
                    kill -9 $CHILD_PID 2>/dev/null
                fi
            done
            # 终止父进程
            kill $PID 2>/dev/null
            sleep 2
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID 2>/dev/null
                echo "✅ Forcibly stopped Flask process: $PID"
            else
                echo "✅ Stopped Flask process: $PID"
            fi
        done
    fi
}

# 执行停止流程
echo "🛑 Beginning shutdown sequence..."

# 尝试多种停止方法
stop_by_pid_file
stop_by_port
stop_by_process_name

# 等待一下让进程完全停止
sleep 3

# 最终检查
echo ""
echo "🔍 Final status check:"

# 检查进程（限制在项目目录下）
FINAL_CELERY_PROCESSES=$(ps aux | grep -E "celery.*worker|celery.*flower" | grep -v grep | grep "$PROJECT_ROOT")
if [ -z "$FINAL_CELERY_PROCESSES" ]; then
    echo "✅ All Celery processes have been stopped"
else
    echo "❌ Remaining Celery processes:"
    echo "$FINAL_CELERY_PROCESSES"
fi

FINAL_FLASK_PROCESSES=$(ps aux | grep -E "python.*app\.py|python.*api\.py" | grep -v grep | grep "$PROJECT_ROOT")
if [ -z "$FINAL_FLASK_PROCESSES" ]; then
    echo "✅ All Flask processes have been stopped"
else
    echo "❌ Remaining Flask processes:"
    echo "$FINAL_FLASK_PROCESSES"
fi

# 检查端口占用
FINAL_FLOWER_PORT=$(lsof -ti:5556 2>/dev/null)
if [ -z "$FINAL_FLOWER_PORT" ]; then
    echo "✅ Port 5556 is now free"
else
    echo "❌ Port 5556 still in use by: $FINAL_FLOWER_PORT"
fi

FINAL_FLASK_PORT=$(lsof -ti:5000 2>/dev/null)
if [ -z "$FINAL_FLASK_PORT" ]; then
    echo "✅ Port 5000 is now free"
else
    echo "❌ Port 5000 still in use by: $FINAL_FLASK_PORT"
fi

echo ""
echo "📁 Log directories with '_stopped' suffix:"
find "$LOG_BASE_DIR" -type d -name "*_stopped*" 2>/dev/null | sort || echo "No stopped directories found"

echo ""
echo "🎉 All services shutdown completed!"