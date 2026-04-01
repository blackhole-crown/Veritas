# API 服务部署指南

本目录包含 Veritas API 服务的部署脚本和配置。

## 🚀 快速部署

### 1. 配置环境变量

```bash
cp .env.template .env
vim .env
```

必填配置：

```bash
# 数据库配置
DB_NAME=veritas_news
DB_USER=your_user
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=your_password

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 模型服务配置（与 run_model 中的端口一致）
QWEN_API_BASE=http://localhost:8006/v1
GTE_API_BASE=http://localhost:9997/v1
```

### 2. 启动服务

```bash
bash start.bash
```

### 3. 停止服务

```bash
bash stop.bash
```

## 📊 服务组件

| 组件 | 说明 | 端口 |
|------|------|------|
| Flask App | API 主服务 | 5000 |
| Celery Worker | 异步任务处理 | - |
| Flower | 任务监控面板 | 5556 |

## 📝 日志文件

日志按日期和时间组织：

```
api/logs/
├── 0305/                     # 日期目录
│   ├── 084151/               # 启动时间目录
│   │   ├── celery_nohup.txt  # Celery 输出
│   │   ├── flask_nohup.txt   # Flask 输出
│   │   ├── flower_nohup.txt  # Flower 输出
│   │   └── start_time.txt    # 启动时间
│   └── 084151_stopped_*      # 停止后归档
```

## 🔧 配置说明

### 修改端口

编辑 `start.bash` 中的 `--port` 参数：

```bash
# Flask 端口（默认 5000）
nohup python app.py > "$LOG_DIR/flask_nohup.txt" 2>&1 &

# Flower 端口（默认 5556）
nohup celery -A $CELERY_APP flower --port=5556 > "$LOG_DIR/flower_nohup.txt" 2>&1 &
```

### 调整并发数

编辑 `start.bash` 中的 `--concurrency` 参数：

```bash
nohup celery -A $CELERY_APP worker --loglevel=info --concurrency=1 > "$LOG_DIR/celery_nohup.txt" 2>&1 &
```

## ❗ 常见问题

### Redis 连接失败

```bash
# 检查 Redis
redis-cli ping

# 启动 Redis
redis-server
```

### 数据库连接失败

```bash
# 检查 PostgreSQL
pg_isready

# 检查 .env 配置
cat .env | grep DB_
```

### 模型服务不可用

```bash
# 检查模型服务
curl http://localhost:8006/v1/chat/completions
curl http://localhost:9997/v1/embeddings

# 确保模型已启动（参考 run_model/README.md）
