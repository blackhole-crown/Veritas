服务器启动postgresql命令：   
sudo systemctl status postgresql

# Postgresql数据库

ip:139.224.18.139:5433，
用户 zhouzehui
密码 zzh050119.
数据库 veritas_news
schema 是默认的 public

psql -h 139.224.18.139 -p 5433 -U zhouzehui -d veritas_news
密码： zzh050119.

_______________________________
- 查看所有表
\dt
- 查看表结构
\d Query
\d Result
\d Cite
- 查看触发器
\dy
_______________________________

测试接口的curl命令
curl -X POST http://localhost:5000/doVeritas \
-H "Content-Type: application/json" \
-d '{"title": "测试标题", "url": "http://example.com"}'


# 查询
    - 获取UUID值
    SELECT uuid FROM Query WHERE title = '';  --替换为实际title

    - 使用获取到的UUID进行查询（替换下面的UUID值）
    SELECT 
        q.uuid AS query_uuid,
        q.title AS original_news,
        r.truth AS verification_result,
        r.content AS evidence_chain,
        c.title AS cited_news_title,
        c.url AS cited_news_url,
        c.relevance,
        c.newstime
    FROM Query q
    JOIN Result r ON q.id = r.query_id
    JOIN Cite c ON r.id = c.result_id
    WHERE q.uuid = '841507ca-1994-5117-b15c-10c81bd22771';  -- 替换为实际UUID
