# Veritas

> 新闻事实核查系统 - 基于 RAG 和知识图谱的智能真伪验证平台

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-brightgreen.svg)](https://www.python.org/dev/peps/pep-0008/)

## 📖 简介

Veritas 是一个基于 RAG（检索增强生成）和知识图谱的新闻事实核查系统。它能够接收新闻标题或 URL，通过搜索引擎获取相关证据，利用知识图谱整合信息，最终由大语言模型生成包含完整证据链和真伪判断的报告。

### 核心特性

- 🔍 **智能检索** - 集成 Brave Search / 同花顺新闻，自动获取相关证据
- 🧠 **知识图谱** - 基于 GraphRAG 构建实体关系网络，深入理解新闻上下文
- 📊 **证据链生成** - LLM 生成结构化的推理过程和真伪判断
- ⏱️ **异步处理** - 基于 Celery 的异步任务队列，确保 API 快速响应
- 🔔 **回调机制** - 支持任务完成后主动推送结果到指定 URL
- 📦 **批量验证** - 支持批量重新验证已有的 claims
- 📈 **任务追踪** - 提供任务状态查询接口，实时获取处理进度

## 🚀 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- CUDA 11.8+ (GPU 加速，推荐 8GB+ 显存)

### 安装

```bash
# 克隆项目
git clone https://github.com/yourname/veritas.git
cd veritas

# 安装依赖
pip install -r requirements.txt
```

详细部署指南请参考：
- [模型部署指南](run_model/README.md)
- [API 服务部署](api/README.md)
- [数据库配置](sql/README.md)

### 启动服务

```bash
# 1. 启动模型服务
cd run_model
# 详见 run_model/README.md

# 2. 启动 API 服务
cd api
bash start.bash
```

### 验证服务

```bash
curl -X POST http://localhost:5000/doVeritas \
  -H "Content-Type: application/json" \
  -d '{"title": "测试新闻标题"}'
```

## 📚 API 文档

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/doVeritas` | 提交新闻验证 |
| GET | `/queryVeritas` | 查询验证结果 |
| GET | `/taskStatus/<task_id>` | 查询任务状态 |
| POST | `/redoVeritas` | 重新验证 |
| POST | `/batchRedoVeritas` | 批量重新验证 |

详细 API 文档见 [api/Document_api.md](api/Document_api.md)

## 📁 项目结构

```
veritas/
├── README.md              # 项目主文档（本文件）
├── LICENSE                # MIT 许可证
├── requirements.txt       # Python 依赖
├── Main.py                # 核心验证逻辑
├── app.py                 # Flask 主应用
├── celery_app.py          # Celery 配置
├── tasks.py               # Celery 任务定义
├── callback_manager.py    # 回调管理器
│
├── api/                   # API 服务
│   ├── README.md          # API 部署文档
│   ├── start.bash         # 启动脚本
│   ├── stop.bash          # 停止脚本
│   └── Document_api.md    # API 接口文档
│
├── run_model/             # 模型服务
│   ├── README.md          # 模型部署文档
│   ├── Qwen3-4B-Instruct/ # Qwen3 模型配置
│   └── Gte-Qwen-2B/       # GTE Embedding 配置
│
├── utils/                 # 工具模块
├── graphrag/              # GraphRAG 配置
├── sql/                   # 数据库脚本
└── env/                   # Conda 环境配置
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

**让 AI 帮你验证新闻真相！** 🚀
