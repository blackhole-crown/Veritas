# 模型下载
from modelscope import snapshot_download

# 将iic/gte_Qwen2-1.5B-instruct 模型下载到指定路径下
# model_dir=snapshot_download('iic/gte_Qwen2-1.5B-instruct',cache_dir='/data/zhouzehui/models')
# model_dir=snapshot_download('Qwen/Qwen2.5-7B-Instruct',cache_dir= '/data/zhouzehui/models')
# 将 Qwen/Qwen2.5-7B-Instruct 模型下载到指定路径 /root/autodl-tmp 下，并使用 master 版本
# model_dir = snapshot_download('Qwen/Qwen2.5-7B-Instruct', cache_dir='/home/zhouzehui/workspace/model', revision='master')
# model_dir = snapshot_download('iic/gte_Qwen2-1.5B-instruct', cache_dir='/data1/zhouzehui/model', revision='master')
# model_dir = snapshot_download('Qwen/Qwen3-4B', cache_dir='/data1/zhouzehui/model', revision='master')
model_dir = snapshot_download('Qwen/Qwen3-4B-Instruct-2507', cache_dir='/data/zhouzehui/models', revision='master')