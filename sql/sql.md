# 1.建表语句

    - 启用UUID扩展
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    - 创建Query表
    CREATE TABLE Query (
        id SERIAL PRIMARY KEY,
        url VARCHAR(1024) NOT NULL,
        title VARCHAR(512) NOT NULL,
        uuid UUID UNIQUE
    );

    - 创建自动生成UUID的触发器函数
    CREATE OR REPLACE FUNCTION generate_query_uuid()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.uuid = uuid_generate_v5('7c4597a0-8fae-4f5f-b28e-50a5e5c5d8f1'::uuid, NEW.id::text);
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    - 创建BEFORE INSERT触发器
    CREATE TRIGGER trigger_generate_query_uuid
    BEFORE INSERT ON Query
    FOR EACH ROW
    EXECUTE FUNCTION generate_query_uuid();

    - 创建Result表
    CREATE TABLE Result (
        id SERIAL PRIMARY KEY,
        title VARCHAR(512) NOT NULL,
        truth BOOLEAN,
        content Varchar(5000),
        knowledge BYTEA,
        query_id INTEGER NOT NULL,
        FOREIGN KEY (query_id) REFERENCES Query(id) ON DELETE CASCADE
    );

    - 创建Cite表
    CREATE TABLE Cite (
        id SERIAL PRIMARY KEY,
        url VARCHAR(1024),
        title VARCHAR(512) NOT NULL,
        relevance INTEGER,
        newstime VARCHAR(20),
        result_id INTEGER NOT NULL,
        FOREIGN KEY (result_id) REFERENCES Result(id) ON DELETE CASCADE
    );

    - 创建索引优化查询性能
    CREATE INDEX idx_cite_result_id ON Cite(result_id);
    CREATE INDEX idx_result_query_id ON Result(query_id);

<!-- -- 
    1. 先移除 url 字段的 NOT NULL 约束
    ALTER TABLE Cite ALTER COLUMN url DROP NOT NULL; 
    测试时候改的，之后改回not null
-->

<!-- -- 
    2. 将 newstime 字段从 DATE 改为 VARCHAR
    ALTER TABLE Cite ALTER COLUMN newstime TYPE VARCHAR(20); 
    测试时候改的，之后改回DATE   
-->

# 2. 插入示例数据
    - 插入Query表数据
    INSERT INTO Query (url, title) VALUES
    ('https://news.example.com/article1', '科学家发现新型可再生能源'),
    ('https://news.example.com/article2', '全球变暖导致北极冰川加速融化');

    - 插入Result表数据（假设Query第一条记录的id=1）
    INSERT INTO Result (title, truth, content, query_id) VALUES
    (
        '科学家发现新型可再生能源', 
        TRUE, 
        '实验数据表明该能源效率达到85%，经多方专家验证可信。',
        1
    );

    - 插入Cite表数据（假设Result记录的id=1）
    INSERT INTO Cite (url, title, relevance, newstime, result_id) VALUES
    (
        'https://science.org/paper1',
        '《自然》期刊：可再生能源研究新突破',
        95,
        '2023-05-15',
        1
    ),
    (
        'https://energy-news.com/report',
        '国际能源署发布年度技术报告',
        88,
        '2023-04-20',
        1
    ),
    (
        'https://tech-review.org/analysis',
        '专家分析：未来十年能源趋势',
        76,
        '2023-06-02',
        1
    );