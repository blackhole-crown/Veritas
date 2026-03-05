# Veritas AI 服务管理手册

## 命令概览
```bash
veritas status      # 查看服务状态
veritas logs        # 查看服务日志
veritas help        # 显示帮助信息
sudo veritas start  # 启动所有AI服务
sudo veritas stop   # 停止所有AI服务
sudo veritas restart # 重启所有服务
```

## 服务说明
- **gte-qwen-2b**: 嵌入模型服务 (端口 9997)
- **qwen3-4b**: 大语言模型服务 (端口 8006)
- **ai-api**: API接口服务 (端口 5000, 5556)

## 快速开始

### 1. 检查服务状态
```bash
veritas status
```

### 2. 启动服务（需要sudo）
```bash
sudo veritas start
```

### 3. 查看启动日志
```bash
veritas logs
```

### 4. 使用API服务
- 主API: http://服务器IP:5000
- 监控界面: http://服务器IP:5556

## 常用场景

### 开发测试
```bash
# 查看服务是否正常运行
veritas status

# 实时查看日志
sudo journalctl -u ai-api -f
```

### 问题排查
```bash
# 查看所有服务日志
veritas logs

# 检查端口占用
netstat -tlnp | grep -E ":(9997|8006|5000|5556)"
```

## 注意事项
- 只有 `start`、`stop`、`restart` 需要 sudo 权限
- 服务启动需要1-2分钟加载模型
- 日志同时保存在系统journal和项目日志目录

## 获取帮助
```bash
veritas help
```
