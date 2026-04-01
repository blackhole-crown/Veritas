# 模型部署指南

本目录包含 Veritas 系统所需模型的部署脚本和配置。

## 📋 模型列表

| 模型 | 用途 | 端口 | 环境 |
|------|------|------|------|
| Qwen3-4B-Instruct-2507 | 大语言模型（LLM） | 8006 | swift |
| gte-Qwen2-1.5B-instruct | 文本嵌入模型（Embedding） | 9997 | xinference |

## 🚀 快速部署

### 1. Qwen3-4B-Instruct-2507

#### 创建虚拟环境

```bash
conda create -n swift python=3.11
conda activate swift
pip install modelscope accelerate
```

#### 下载模型

```bash
python -c "
from modelscope import snapshot_download
snapshot_download('Qwen/Qwen3-4B-Instruct-2507', 
                  cache_dir='/path/to/models', 
                  revision='master')
"
```

#### 安装 Swift

```bash
cd resource/ms-swift
pip install -e .[llm]
pip install "vllm>=0.6.1"
```

#### 启动服务

```bash
conda activate swift
cd Qwen3-4B-Instruct

# 方式一：直接启动
CUDA_VISIBLE_DEVICES=0 \
swift deploy \
  --model_type qwen2_5 \
  --model /path/to/models/Qwen/Qwen3-4B-Instruct-2507 \
  --infer_backend vllm \
  --gpu_memory_utilization 0.91 \
  --temperature 0 \
  --tensor_parallel_size 1 \
  --host 127.0.0.1 \
  --port 8006 \
  --max_num_seqs 4 \
  --max_model_len 9216

# 方式二：后台运行
bash nohup_qwen3.bash

# 停止服务
bash stop.bash
```

### 2. GTE-Qwen2 Embedding 模型

#### 创建虚拟环境

```bash
conda create --name xinference python=3.10.9
conda activate xinference
pip install "xinference[transformers]" sentence-transformers
```

#### 下载模型

```bash
python -c "
from modelscope import snapshot_download
snapshot_download('iic/gte_Qwen2-1.5B-instruct', 
                  cache_dir='/path/to/models', 
                  revision='master')
"
```

#### 启动服务

```bash
conda activate xinference
cd Gte-Qwen-2B

# 方式一：直接启动（需两个终端）
# 终端1：启动 Xinference 服务
xinference-local --host 0.0.0.0 --port 9997

# 终端2：部署模型
xinference launch \
  --model-name gte-Qwen2 \
  --model-type embedding \
  --replica 1 \
  --n-gpu auto \
  --gpu-idx 0 \
  --model-path /path/to/models/gte_Qwen2-1_5B-instruct

# 方式二：后台运行
bash nohup_xinference.bash

# 停止服务
bash stop.bash
```

## 🧪 测试模型

### 测试 Qwen3

```bash
curl -X POST http://127.0.0.1:8006/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-4B-Instruct-2507",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100,
    "temperature": 0
  }'
```

### 测试 Embedding

```bash
curl -X POST http://0.0.0.0:9997/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gte-Qwen2",
    "input": "测试文本"
  }'
```

## 📁 目录结构

```
run_model/
├── README.md                 # 本文件
├── Qwen3-4B-Instruct/        # Qwen3 模型
│   ├── nohup_qwen3.bash      # 后台启动脚本
│   ├── stop.bash             # 停止脚本
│   ├── qwen3.sh              # 模型启动配置
│   └── environment_swift.yaml
└── Gte-Qwen-2B/              # GTE Embedding 模型
    ├── nohup_xinference.bash # 后台启动脚本
    ├── stop.bash             # 停止脚本
    ├── xinference.sh         # 模型启动配置
    └── environment_xinference.yaml
```

## 🔧 配置说明

### 修改模型路径

编辑 `Qwen3-4B-Instruct/qwen3.sh`：

```bash
--model /your/actual/model/path/Qwen/Qwen3-4B-Instruct-2507
```

编辑 `Gte-Qwen-2B/xinference.sh`：

```bash
--model-path /your/actual/model/path/gte_Qwen2-1_5B-instruct
```

### 修改端口

- Qwen3: 修改 `--port` 参数
- Xinference: 修改 `--port` 参数
- 同步修改 `graphrag/sample/settings.yaml` 中的 `api_base` 地址

## ❗ 常见问题

### 端口被占用

```bash
# 查看端口占用
lsof -i:8006
lsof -i:9997

# 修改端口后需同步修改 settings.yaml
```

### CUDA 内存不足

- 减小 `gpu_memory_utilization` 参数
- 减小 `max_model_len` 参数
- 使用更小的模型

### 模型下载失败

- 检查网络连接
- 尝试更换镜像源
- 使用手动下载后放入指定目录


