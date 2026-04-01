# 代理
source /etc/profile.d/clash.sh

- 开启代理
proxy_on

- 测试代理
curl -I https://www.google.com

- 关闭代理
proxy_off



# 数据库操作
- 连接
psql -h 139.224.18.139 -p 5433 -U zhouzehui -d veritas_news

- 查询
\dt 查看表结构

SELECT * FROM Query;
<!-- SELECT * FROM Result; -->
SELECT id,title,truth,knowledge,query_id FROM Result;
SELECT * FROM cite;

SELECT content FROM Result where query_id = 21;

# 测试模型部署

- Qwen2_5-7B-Instruct
curl -X POST http://127.0.0.1:8005/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "Qwen2_5-7B-Instruct",
  "messages": [
    {
      "role": "user",
      "content": "判断以下新闻的真实性，仅输出TRUE或FALSE：中华人民共和国成立于1948年"
    }
  ],
  "max_tokens": 1024,
  "temperature": 0
}'

- gte-Qwen2
curl -X POST http://0.0.0.0:9997/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gte-Qwen2",
    "input": "/home/zhouzehui/workspace/workspace/addon_v1_qwen3_api/run_model/Gte-Qwen-2B/nohup_xinference.bash"
}'

- Qwen3-4B-Instruct-2507
curl -X POST http://127.0.0.1:8006/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "Qwen3-4B-Instruct-2507",
  "messages": [
    {
      "role": "user",
      "content": "告诉我2025年12月21日的天气"
    }
  ],
  "max_tokens": 1024,
  "temperature": 0
}'


curl -X POST http://127.0.0.1:8006/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "Qwen3-4B-Instruct-2507",
  "messages": [
    {
      "role": "user",
      "content": "判断下面这个claim是否属于新闻，仅输出TRUE或FALSE\n\"claim\"：CPO概念股多股跳水，新易盛、中际旭创跌超5%"
    }
  ],
  "max_tokens": 1024,
  "temperature": 0
}'


curl -X POST http://127.0.0.1:8006/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "Qwen3-4B-Instruct-2507",
  "messages": [
    {
      "role": "user",
      "content": "判断下面这个claim是否属于新闻，并给出理由\n\"claim\"：CPO概念股多股跳水，新易盛、中际旭创跌超5%"
    }
  ],
  "max_tokens": 1024,
  "temperature": 50
}'


curl -X POST http://127.0.0.1:8888/api/news \
  -H "Content-Type: application/json" \
  -d '{
    "id": 9999,
    "description": "测试新闻标题：Gemini准确率从21%飙到97%",
    "history": {
      "k=5": [
        {
          "Date": "2026-03-05",
          "Result": "FALSE"
        }
      ],
      "k=10": [],
      "k=15": [],
      "k=20": []
    },
    "last_output": {
      "k=5": "#### **1. COLLECTION**\n**Record ALL Analyst Reports one by one:**\n- **Analyst Report 1 (Importance Score: 100)**: Test report content\n\n**+more**\n\n---\n\n#### **2. ANALYSIS**\n**Evaluation of ALL recorded Analyst Reports one by one:**\n- **Analyst Report 1 (Importance Score: 100)**: Test analysis\n\n**Evidence Synthesis and Corroboration:**\n- Evidence 1\n\n---\n\n#### **3. CONCLUSION**\n### **Final Judgment**\n**FALSE**\n\n**Detailed Reasons for False Classification:**\nⅠ. **Test Reason**\nTest content\n\n**NEWS TYPE**\n[Test]",
      "k=10": "",
      "k=15": "",
      "k=20": ""
    },
    "revelent_news": {
      "id": 9999,
      "claim": "测试新闻标题",
      "collection": [
        {
          "id": 1,
          "title": "相关新闻1",
          "url": "url:https://example.com/news1"
        }
      ]
    }
  }'




* 若有端口冲突请修改，并修改graphrag/sample/settings.yaml的端口
* 若要更换模型，请重新配置bash文件



# 解决僵尸进程
ps -o pid,ppid -p ppid
kill -9 ppid


# 查看挂载的程序uid
ps -ef | grep "bash run_model/Qwen3-4B-Instruct/qwen3.sh" | grep -v grep   
# bash run_model/qwen3.sh   python app.py

zhouzeh+ 3863946       1  0 Oct13 ?        00:00:01 python api/api.py
zhouzeh+ 3863964 3863946  0 Oct13 ?        00:09:05 /home/zhouzehui/miniconda3/envs/addon_v1/bin/python api/api.py

- 先终止子进程,再终止父进程
kill 3863964
kill 3863946






<!-- # 挂载接口
conda activate addon_v1
python api/api.py

- 挂载后台
nohup python api/api.py > run_model/nohup/api/1013/nohup.txt 2> run_model/nohup/api/1013/error.txt & -->

