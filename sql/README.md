服务器启动postgresql命令：   
sudo systemctl status postgresql

# Postgresql数据库

ip:139.224.18.139:5433，(修改为本机ip地址和端口)
用户 Veritas
密码 Veritas
数据库 veritas_news
schema 是默认的 public

psql -h 139.224.18.139 -p 5433 -U Veritas -d veritas_news
密码： Veritas



# 创建表
# 进入目录
cd sql
# 1. 在新服务器上创建数据库和用户
sudo -u postgres psql << 'EOF'
CREATE USER Veritas WITH PASSWORD 'Veritas';
CREATE DATABASE veritas_news OWNER Veritas;
GRANT ALL PRIVILEGES ON DATABASE veritas_news TO Veritas;
EOF

# 2. 执行建表语句
psql -h localhost -p 5433 -U Veritas -d veritas_news -f create_table.sql

# 3. 验证表结构
psql -h localhost -p 5433 -U Veritas -d veritas_news -c "\d Query"
psql -h localhost -p 5433 -U Veritas -d veritas_news -c "\d Result"
psql -h localhost -p 5433 -U Veritas -d veritas_news -c "\d Cite"

配置好后，记得同步修改utils/sql.py的连接池

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
