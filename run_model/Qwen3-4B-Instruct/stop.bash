#!/bin/bash
BASE_DIR="../../.."
LOG_BASE_DIR="./run_model/nohup/Qwen3_4B-Instruct"
PORT=8006

echo "=========================================="
echo "🛑 Stopping Qwen3 Service Completely"
echo "=========================================="

stop_by_pid_file() {
    local LATEST_DIR=$(find "$LOG_BASE_DIR" -name "pid.txt" -type f 2>/dev/null | xargs dirname | sort | tail -1)
    
    if [ -z "$LATEST_DIR" ]; then
        echo "ℹ️  No PID file found, trying other methods..."
        return 1
    fi

    PID_FILE="$LATEST_DIR/pid.txt"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "📁 Found service directory: $LATEST_DIR"
        echo "🎯 Found PID from file: $PID"

        if ps -p $PID > /dev/null; then
            echo "⏳ Stopping process tree for PID: $PID"

            kill -- -$(ps -o pgid= $PID | grep -o '[0-9]*') 2>/dev/null
            sleep 2

            if ps -p $PID > /dev/null; then
                echo "⚠️  Process still running, forcing kill..."
                kill -9 $PID 2>/dev/null
            fi
            
            echo "✅ Process stopped"
        else
            echo "ℹ️  Process not running (PID: $PID)"
        fi

        STOPPED_DIR="${LATEST_DIR}_stopped_$(date +%H%M%S)"
        mv "$LATEST_DIR" "$STOPPED_DIR" 2>/dev/null && echo "📁 Moved to: $STOPPED_DIR"
        
        return 0
    else
        echo "❌ PID file not found in latest directory"
        return 1
    fi
}

stop_by_port() {
    echo "🔍 Checking processes using port $PORT..."
    
    PORT_PIDS=$(lsof -ti:$PORT 2>/dev/null)
    
    if [ -z "$PORT_PIDS" ]; then
        echo "ℹ️  No processes found using port $PORT"
        return 1
    fi
    
    for PID in $PORT_PIDS; do
        echo "🎯 Found process using port $PORT: PID=$PID"
        echo "Process info:"
        ps -p $PID -o pid,ppid,cmd --no-headers 2>/dev/null || echo "Cannot get process info"
        
        PGID=$(ps -o pgid= $PID 2>/dev/null | tr -d ' ')
        if [ ! -z "$PGID" ]; then
            echo "⏳ Killing process group: -$PGID"
            kill -- -$PGID 2>/dev/null
        else
            kill $PID 2>/dev/null
        fi
        sleep 1
        
        if ps -p $PID > /dev/null; then
            echo "⚠️  Forcing kill PID: $PID"
            kill -9 $PID 2>/dev/null
        fi
        
        echo "✅ Stopped process: $PID"
    done
    
    return 0
}

stop_by_process_name() {
    echo "🔍 Checking for Qwen3 related processes..."
    
    QWEN_PROCESSES=$(ps aux | grep -E "qwen3.sh|python.*8006|uvicorn.*8006" | grep -v grep | awk '{print $2}')
    
    if [ -z "$QWEN_PROCESSES" ]; then
        echo "ℹ️  No Qwen3 related processes found"
        return 1
    fi
    
    for PID in $QWEN_PROCESSES; do
        echo "🎯 Found Qwen3 process: PID=$PID"
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

cleanup_residual() {
    echo "🧹 Cleaning up residual processes..."
    
    PORT_PIDS=$(lsof -ti:$PORT 2>/dev/null)
    if [ ! -z "$PORT_PIDS" ]; then
        echo "⚠️  Residual processes on port $PORT: $PORT_PIDS"
        for PID in $PORT_PIDS; do
            kill -9 $PID 2>/dev/null
            echo "✅ Killed residual process: $PID"
        done
    fi
    
    NOHUP_PROCESSES=$(ps aux | grep "nohup.*qwen3" | grep -v grep | awk '{print $2}')
    if [ ! -z "$NOHUP_PROCESSES" ]; then
        for PID in $NOHUP_PROCESSES; do
            kill -9 $PID 2>/dev/null
            echo "✅ Killed nohup process: $PID"
        done
    fi
}

# 主停止流程
echo "🛑 Beginning shutdown sequence..."

# 1. 首先尝试通过PID文件停止
stop_by_pid_file

# 2. 如果PID文件方法失败，尝试通过端口停止
if [ $? -ne 0 ]; then
    echo "🔄 Trying port-based shutdown..."
    stop_by_port
fi

# 3. 如果端口方法也失败，尝试通过进程名停止
if [ $? -ne 0 ]; then
    echo "🔄 Trying process name-based shutdown..."
    stop_by_process_name
fi

# 4. 清理残留进程
cleanup_residual

# 最终检查
echo ""
echo "🔍 Final status check..."

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
FINAL_PROCESSES=$(ps aux | grep -E "qwen3.sh|python.*8006" | grep -v grep)
if [ -z "$FINAL_PROCESSES" ]; then
    echo "✅ All Qwen3 processes have been stopped"
else
    echo "❌ Remaining Qwen3 processes:"
    echo "$FINAL_PROCESSES"
fi

echo ""
echo "🎉 Shutdown completed!"