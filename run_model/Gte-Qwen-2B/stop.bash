#!/bin/bash

# 设置基础路径（从脚本位置计算）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"  # 上两级目录到 addon_v1_qwen3_api
RUN_MODEL_DIR="$BASE_DIR/run_model"
LOG_BASE_DIR="$RUN_MODEL_DIR/nohup/Xinference"
PORT=9997

echo "=========================================="
echo "🛑 Stopping Xinference Service Completely"
echo "=========================================="
echo "📁 Base Directory: $BASE_DIR"

# 方法1：通过PID文件停止
stop_by_pid_file() {
    local pid_files=$(find "$LOG_BASE_DIR" -name "*.pid.txt" -type f 2>/dev/null)
    if [ -z "$pid_files" ]; then
        echo "ℹ️  No PID file found, trying other methods..."
        return 1
    fi

    local LATEST_DIR=$(echo "$pid_files" | xargs dirname | sort | tail -1)
    
    if [ -z "$LATEST_DIR" ]; then
        echo "ℹ️  No PID file found, trying other methods..."
        return 1
    fi

    echo "📁 Found service directory: $LATEST_DIR"
    
    # 停止 Xinference 服务进程
    XINFERENCE_PID_FILE="$LATEST_DIR/xinference_pid.txt"
    if [ -f "$XINFERENCE_PID_FILE" ]; then
        XINFERENCE_PID=$(cat "$XINFERENCE_PID_FILE")
        echo "🎯 Found Xinference Service PID: $XINFERENCE_PID"
        
        if ps -p $XINFERENCE_PID > /dev/null; then
            echo "⏳ Stopping Xinference Service process: $XINFERENCE_PID"
            kill -- -$(ps -o pgid= $XINFERENCE_PID | grep -o '[0-9]*') 2>/dev/null
            sleep 2
            
            if ps -p $XINFERENCE_PID > /dev/null; then
                echo "⚠️  Xinference Service process still running, forcing kill..."
                kill -9 $XINFERENCE_PID 2>/dev/null
            fi
            
            echo "✅ Xinference Service process stopped"
        else
            echo "ℹ️  Xinference Service process not running (PID: $XINFERENCE_PID)"
        fi
    fi
    
    # 停止模型部署进程
    MODEL_PID_FILE="$LATEST_DIR/model_pid.txt"
    if [ -f "$MODEL_PID_FILE" ]; then
        MODEL_PID=$(cat "$MODEL_PID_FILE")
        echo "🎯 Found Model Deployment PID: $MODEL_PID"
        
        if ps -p $MODEL_PID > /dev/null; then
            echo "⏳ Stopping Model Deployment process: $MODEL_PID"
            kill -- -$(ps -o pgid= $MODEL_PID | grep -o '[0-9]*') 2>/dev/null
            sleep 2
            
            if ps -p $MODEL_PID > /dev/null; then
                echo "⚠️  Model Deployment process still running, forcing kill..."
                kill -9 $MODEL_PID 2>/dev/null
            fi
            
            echo "✅ Model Deployment process stopped"
        else
            echo "ℹ️  Model Deployment process not running (PID: $MODEL_PID)"
        fi
    fi
    
    # 重命名目录表示已停止
    STOPPED_DIR="${LATEST_DIR}_stopped_$(date +%H%M%S)"
    mv "$LATEST_DIR" "$STOPPED_DIR" 2>/dev/null && echo "📁 Moved to: $STOPPED_DIR"
    
    return 0
}

# 方法2：通过端口停止
stop_by_port() {
    echo "🔍 Checking processes using port $PORT..."
    
    # 查找使用9997端口的进程
    PORT_PIDS=$(lsof -ti:$PORT 2>/dev/null)
    
    if [ -z "$PORT_PIDS" ]; then
        echo "ℹ️  No processes found using port $PORT"
        return 1
    fi
    
    for PID in $PORT_PIDS; do
        echo "🎯 Found process using port $PORT: PID=$PID"
        echo "Process info:"
        ps -p $PID -o pid,ppid,cmd --no-headers 2>/dev/null || echo "Cannot get process info"
        
        # 杀死进程及其进程组
        PGID=$(ps -o pgid= $PID 2>/dev/null | tr -d ' ')
        if [ ! -z "$PGID" ]; then
            echo "⏳ Killing process group: -$PGID"
            kill -- -$PGID 2>/dev/null
        else
            kill $PID 2>/dev/null
        fi
        sleep 1
        
        # 强制杀死如果还在运行
        if ps -p $PID > /dev/null; then
            echo "⚠️  Forcing kill PID: $PID"
            kill -9 $PID 2>/dev/null
        fi
        
        echo "✅ Stopped process: $PID"
    done
    
    return 0
}

# 方法3：通过进程名停止
stop_by_process_name() {
    echo "🔍 Checking for Xinference related processes..."
    
    # 查找可能的Xinference相关进程
    XINFERENCE_PROCESSES=$(ps aux | grep -E "xinference-local|xinference.sh|python.*9997|uvicorn.*9997" | grep -v grep | awk '{print $2}')
    
    if [ -z "$XINFERENCE_PROCESSES" ]; then
        echo "ℹ️  No Xinference related processes found"
        return 1
    fi
    
    for PID in $XINFERENCE_PROCESSES; do
        echo "🎯 Found Xinference process: PID=$PID"
        echo "Process info:"
        ps -p $PID -o pid,ppid,cmd --no-headers 2>/dev/null
        
        # 杀死进程
        kill $PID 2>/dev/null
        sleep 1
        
        if ps -p $PID > /dev/null; then
            kill -9 $PID 2>/dev/null
            echo "✅ Forcibly stopped process: $PID"
        else
            echo "✅ Stopped process: $PID"
        fi
    done
    
    return 0
}

# 方法4：清理残留进程
cleanup_residual() {
    echo "🧹 Cleaning up residual processes..."
    
    # 再次检查端口
    PORT_PIDS=$(lsof -ti:$PORT 2>/dev/null)
    if [ ! -z "$PORT_PIDS" ]; then
        echo "⚠️  Residual processes on port $PORT: $PORT_PIDS"
        for PID in $PORT_PIDS; do
            kill -9 $PID 2>/dev/null
            echo "✅ Killed residual process: $PID"
        done
    fi
    
    # 检查nohup相关进程
    NOHUP_PROCESSES=$(ps aux | grep -E "nohup.*xinference|nohup.*gte" | grep -v grep | awk '{print $2}')
    if [ ! -z "$NOHUP_PROCESSES" ]; then
        for PID in $NOHUP_PROCESSES; do
            kill -9 $PID 2>/dev/null
            echo "✅ Killed nohup process: $PID"
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

# 清理残留
cleanup_residual

# 最终检查
echo ""
echo "🔍 Final status check:"

# 检查端口
FINAL_PORT_PIDS=$(lsof -ti:$PORT 2>/dev/null)
if [ -z "$FINAL_PORT_PIDS" ]; then
    echo "✅ Port $PORT is now free"
else
    echo "❌ Port $PORT still in use by: $FINAL_PORT_PIDS"
    for PID in $FINAL_PORT_PIDS; do
        kill -9 $PID 2>/dev/null
        echo "✅ Killed remaining process: $PID"
    done
fi

# 检查进程
FINAL_PROCESSES=$(ps aux | grep -E "xinference-local|xinference.sh|gte-qwen" | grep -v grep)
if [ -z "$FINAL_PROCESSES" ]; then
    echo "✅ All Xinference processes have been stopped"
else
    echo "❌ Remaining Xinference processes:"
    echo "$FINAL_PROCESSES"
fi

echo ""
echo "🎉 Xinference shutdown completed!"