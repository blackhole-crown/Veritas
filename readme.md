# 部署
查看run_model/readme.md

# 部署模型
bash run_model/Qwen3-4B-Instruct/nohup_qwen3.bash
bash run_model/Gte-Qwen-2B/nohup_xinference.bash





# 测试接口

- doVeritas

curl -X POST http://localhost:5000/doVeritas \
  -H "Content-Type: application/json" \
  -d '{
    "title": "美国与伊朗开战le",
    "url":"",
    "source": "Router"
  }'


- queryVeritas

curl -X GET "http://localhost:5000/queryVeritas?claim=9200a331-9e03-55a6-a46b-5c0b7b2a030e"

claude --plugin-dir ./connect-apps-plugin























# 服务器
1. clash安装目录
/root/clash-for-linux

2. 普通用户设置代理
Clash Dashboard 访问地址: http://<ip>:9090/ui
Secret: 907b33965502fe434180cf1e42a1f1ef9f52bf349276d923efa448a760252353
请执行以下命令加载环境变量: source /etc/profile.d/clash.sh
请执行以下命令开启系统代理: proxy_on
若要临时关闭系统代理，请执行: proxy_off
查看代理环境变量: env | grep -E 'http_proxy|https_proxy'
测试Google: curl -I https://www.google.com

3. 数据（模型）存储路径，公有数据建议存储到/data/zycj，下载模型尽量使用modelscope,使用阿里内部网络，速度很快，现有模型如下：
/data/zycj
└── models
    ├── Helsinki-NLP
    └── Qwen
        ├── Qwen2.5-32B-Instruct-AWQ
        ├── Qwen2.5-VL-3B-Instruct
        └── Qwen2.5-VL-7B-Instruct


# 目录结构
addon/
├── app.py                 # 原来的主应用文件
├── celery_app.py          # Celery 配置
├── tasks.py               # Celery 任务定义
├── Main.py
├── utils/
│   ├── __init__.py
│   ├── sql.py
│   └── utils.py
└── requirements.txt






## 表示一个进度
仅对于“浪浪山小妖怪的新闻”解决了进制转换和时间错位的问题，不过仍然存在名称翻译的问题，提示词ai生成好了还未修改
现在正想要扩展新闻，试试看之前的提示词修改后是否对别的错误判断的新闻适用，还需要解决的问题是输出规范问题，输出格式已经变了，好在备份了之前的，前面200条都是按照老的提示词泡出来的结果
是用新的提示词后最好全部重新跑，在管数据库和别的问题，还有一个遗留的就是local和global的问题，之前没改提示词试了使用global，效果是一样的，仍然是使用模型自己训练的数据集作为背景

- 1010
接口测试成功，问题在于跑出的结果未能成功插入数据库√

- 1011
有个想法就是，不在Main里面方origin_judge,而是只在接口里使用√

insert_result成功

- 1013
插入数据库之前，把claim清洗一下






















































