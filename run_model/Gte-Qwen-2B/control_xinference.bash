#!/bin/bash

# Xinference 服务控制脚本
# 使用方法: ./control_xinference.sh [start|stop|status]

# 设置基础路径（从脚本位置计算）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
START_SCRIPT="$BASE_DIR/run_model/Gte-Qwen-2B/nohup_xinference.bash"
STOP_SCRIPT="$BASE_DIR/run_model/Xinference/stop.bash"
PORT=9997

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色信息
info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# 显示使用说明
show_help() {
    echo "=========================================="
    echo "🤖 Xinference 服务控制脚本"
    echo "=========================================="
    echo "使用方法: $0 [command]"
    echo ""
    echo "命令列表:"
    echo "  start   - 启动 Xinference 服务"
    echo "  stop    - 停止 Xinference 服务" 
    echo "  status  - 查看服务状态"
    echo "  help    - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动服务"
    echo "  $0 stop     # 停止服务"
    echo "  $0 status   # 查看状态"
    echo ""
    echo "服务信息:"
    echo "  🌐 访问地址: http://0.0.0.0:9997"
    echo "  📁 模型: Gte-Qwen-1.5B"
    echo "=========================================="
}

# 检查服务状态
check_status() {
    info "检查 Xinference 服务状态..."
    
    # 检查端口占用
    PORT_PIDS=$(lsof -ti:$PORT 2>/dev/null)
    if [ ! -z "$PORT_PIDS" ]; then
        success "Xinference 服务正在运行 (端口: $PORT)"
        echo ""
        echo "进程信息:"
        for PID in $PORT_PIDS; do
            ps -p $PID -o pid,user,%cpu,%mem,cmd --no-headers 2>/dev/null
        done
        
        # 检查最新的日志目录
        LATEST_DIR=$(find "$BASE_DIR/run_model/nohup/Xinference" -name "*.pid.txt" -type f 2>/dev/null | xargs dirname | sort | tail -1 2>/dev/null)
        if [ ! -z "$LATEST_DIR" ] && [ -d "$LATEST_DIR" ]; then
            echo ""
            info "服务详细信息:"
            if [ -f "$LATEST_DIR/start_time.txt" ]; then
                echo "  启动时间: $(cat $LATEST_DIR/start_time.txt)"
            fi
            if [ -f "$LATEST_DIR/xinference_pid.txt" ]; then
                echo "  Xinference 服务 PID: $(cat $LATEST_DIR/xinference_pid.txt)"
            fi
            if [ -f "$LATEST_DIR/model_pid.txt" ]; then
                echo "  模型部署 PID: $(cat $LATEST_DIR/model_pid.txt)"
            fi
            echo "  日志目录: $LATEST_DIR"
        fi
        
        # 检查模型是否注册
        echo ""
        info "检查模型注册状态..."
        if curl -s http://0.0.0.0:9997/v1/models > /dev/null 2>&1; then
            MODEL_LIST=$(curl -s http://0.0.0.0:9997/v1/models 2>/dev/null)
            if echo "$MODEL_LIST" | grep -q "gte-Qwen2"; then
                success "模型 gte-Qwen2 已注册"
            else
                warning "模型 gte-Qwen2 未注册"
            fi
        else
            error "无法连接 Xinference API"
        fi
        
        echo ""
        info "服务访问地址: http://0.0.0.0:9997"
        return 0
    else
        warning "Xinference 服务未运行 (端口: $PORT)"
        return 1
    fi
}

# 启动服务
start_service() {
    info "正在启动 Xinference 服务..."
    
    # 检查是否已在运行
    if check_status > /dev/null 2>&1; then
        warning "服务已经在运行中!"
        echo "如果需要重启，请先执行: $0 stop"
        return 1
    fi
    
    # 检查启动脚本是否存在
    if [ ! -f "$START_SCRIPT" ]; then
        error "启动脚本不存在: $START_SCRIPT"
        return 1
    fi
    
    # 检查启动脚本是否有执行权限
    if [ ! -x "$START_SCRIPT" ]; then
        warning "启动脚本没有执行权限，正在添加..."
        chmod +x "$START_SCRIPT"
    fi
    
    # 执行启动脚本
    info "执行启动脚本..."
    cd "$(dirname "$START_SCRIPT")"
    bash "$(basename "$START_SCRIPT")"
    
    # 等待几秒后检查状态
    sleep 10
    if check_status > /dev/null 2>&1; then
        success "Xinference 服务启动成功!"
    else
        error "Xinference 服务启动可能失败，请检查日志"
    fi
}

# 停止服务
stop_service() {
    info "正在停止 Xinference 服务..."
    
    # 检查是否在运行
    if ! check_status > /dev/null 2>&1; then
        warning "服务未在运行，无需停止"
        return 0
    fi
    
    # 检查停止脚本是否存在
    if [ ! -f "$STOP_SCRIPT" ]; then
        error "停止脚本不存在: $STOP_SCRIPT"
        return 1
    fi
    
    # 检查停止脚本是否有执行权限
    if [ ! -x "$STOP_SCRIPT" ]; then
        warning "停止脚本没有执行权限，正在添加..."
        chmod +x "$STOP_SCRIPT"
    fi
    
    # 执行停止脚本
    info "执行停止脚本..."
    cd "$(dirname "$STOP_SCRIPT")"
    bash "$(basename "$STOP_SCRIPT")"
    
    # 等待几秒后检查状态
    sleep 3
    if ! check_status > /dev/null 2>&1; then
        success "Xinference 服务已停止!"
    else
        error "Xinference 服务停止可能失败，请手动检查"
    fi
}

# 主程序
case "$1" in
    "start")
        start_service
        ;;
    "stop")
        stop_service
        ;;
    "status")
        check_status
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    "")
        error "请提供命令参数"
        show_help
        exit 1
        ;;
    *)
        error "未知命令: $1"
        show_help
        exit 1
        ;;
esac