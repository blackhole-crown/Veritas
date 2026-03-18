-- 1. 启用UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. 创建Query表（包含source字段）
CREATE TABLE Query (
    id SERIAL PRIMARY KEY,
    url VARCHAR(1024) NOT NULL,
    title VARCHAR(512) NOT NULL,
    uuid UUID UNIQUE,
    source VARCHAR(255) DEFAULT NULL
);

-- 3. 创建UUID生成函数
CREATE OR REPLACE FUNCTION generate_query_uuid()
RETURNS TRIGGER AS $$
BEGIN
    NEW.uuid = uuid_generate_v5('7c4597a0-8fae-4f5f-b28e-50a5e5c5d8f1'::uuid, NEW.id::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. 创建触发器
CREATE TRIGGER trigger_generate_query_uuid
BEFORE INSERT ON Query
FOR EACH ROW
EXECUTE FUNCTION generate_query_uuid();

-- 5. 创建Result表（包含status, error_message, created_at, updated_at字段）
CREATE TABLE Result (
    id SERIAL PRIMARY KEY,
    title VARCHAR(512) NOT NULL,
    truth BOOLEAN,
    content VARCHAR(20000),
    knowledge BYTEA,
    query_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (query_id) REFERENCES Query(id) ON DELETE CASCADE
);

-- 6. 创建Cite表
CREATE TABLE Cite (
    id SERIAL PRIMARY KEY,
    url VARCHAR(1024),
    title VARCHAR(512) NOT NULL,
    relevance INTEGER,
    newstime VARCHAR(20),
    result_id INTEGER NOT NULL,
    FOREIGN KEY (result_id) REFERENCES Result(id) ON DELETE CASCADE
);

-- 7. 创建所有索引
CREATE INDEX idx_cite_result_id ON Cite(result_id);
CREATE INDEX idx_result_query_id ON Result(query_id);
CREATE INDEX idx_result_created_at ON Result(created_at);
CREATE INDEX idx_result_status ON Result(status);

-- 8. 如果需要自动更新updated_at，可以创建触发器（可选）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_result_updated_at
BEFORE UPDATE ON Result
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();