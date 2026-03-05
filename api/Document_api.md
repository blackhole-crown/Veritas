# Veritas 新闻验证系统 API 文档

## 基础信息
- **基础URL**: `http://139.224.18.139:5000`
- **编码**: UTF-8
- **响应格式**: JSON

## 接口概览

### 1. 新闻验证接口
- `POST /doVeritas` - 提交新闻验证请求
- `GET /queryVeritas` - 查询验证结果
- `POST /redoVeritas` - 重新验证已有claim
- `POST /batchRedoVeritas` - 批量重新验证

### 2. 任务状态查询
- `GET /taskStatus/<task_id>` - 查询Celery任务状态

### 3. 回调管理接口
- `POST /setGlobalCallback` - 设置全局回调URL
- `POST /registerCallback` - 为特定claim注册回调
- `GET /callbackStatus/<claim_uuid>` - 查询回调状态
- `GET /callbackStatistics` - 获取回调统计信息
- `POST /clearCallback/<claim_uuid>` - 清除特定claim回调配置

---

## 接口详情

### 1. 提交新闻验证请求
**POST** `/doVeritas`

#### 请求体
```json
{
  "title": "新闻标题",
  "url": "新闻链接（可选）",
  "callback_url": "回调地址（可选）",
  "callback_secret": "回调密钥（可选）"
}
```

#### 响应体 - 成功 (200)
```json
{
  "status": 200,
  "message": "OK",
  "data": {
    "claim": "生成的UUID",
    "veritas": "初步验证结果",
    "task_id": "Celery任务ID",
    "callback_registered": true/false,
    "callback_url": "注册的回调地址（如有）"
  }
}
```

#### 响应体 - 错误 (400/500)
```json
{
  "status": 400/500,
  "message": "错误描述"
}
```

---

### 2. 查询验证结果
**GET** `/queryVeritas?claim=<uuid>`

#### 请求参数
- `claim` (必需): 之前生成的UUID

#### 响应体 - 成功 (200)
```json
{
  "status": 200,
  "message": "OK",
  "data": {
    "content": "markdown格式的证据链论证",
    "reference": [
      {
        "title": "相关链接标题1",
        "url": "相关链接1",
        "newstime": "YYYY-MM-DD"
      },
      {
        "title": "相关链接标题2",
        "url": "相关链接2",
        "newstime": "YYYY-MM-DD"
      }
    ]
  }
}
```

---

### 3. 查询任务状态
**GET** `/taskStatus/<task_id>`

#### 响应体示例
```json
{
  "task_id": "任务ID",
  "status": "PENDING/STARTED/RETRY/FAILURE/SUCCESS",
  "result": "任务结果（成功时）",
  "error": "错误信息（失败时）"
}
```

---

### 4. 重新验证已有claim
**POST** `/redoVeritas`

#### 请求体
```json
{
  "claim": "已有的UUID",
  "callback_url": "新的回调地址（可选）",
  "callback_secret": "新的回调密钥（可选）"
}
```

#### 响应体 - 成功 (200)
```json
{
  "status": 200,
  "message": "OK",
  "data": {
    "claim": "UUID",
    "new_task_id": "新的任务ID",
    "callback_registered": true/false,
    "callback_url": "回调地址（如有）",
    "message": "Verification restarted successfully"
  }
}
```

---

### 5. 批量重新验证
**POST** `/batchRedoVeritas`

#### 请求体
```json
{
  "claims": ["uuid1", "uuid2", "uuid3"],
  "callback_url": "批量回调地址（可选）",
  "callback_secret": "批量回调密钥（可选）"
}
```

#### 响应体 - 成功 (200)
```json
{
  "status": 200,
  "message": "Batch processing completed: X started, Y failed",
  "data": {
    "total": 3,
    "started": 2,
    "failed": 1,
    "results": [
      {
        "claim": "uuid1",
        "status": "started",
        "task_id": "任务ID",
        "message": "Verification restarted"
      },
      {
        "claim": "uuid2",
        "status": "failed",
        "message": "错误信息"
      }
    ]
  }
}
```

---

### 6. 设置全局回调
**POST** `/setGlobalCallback`

#### 请求体
```json
{
  "callback_url": "全局回调地址",
  "secret_key": "密钥（可选）"
}
```

#### 响应体 - 成功 (200)
```json
{
  "status": 200,
  "message": "Global callback URL set successfully",
  "data": {
    "callback_url": "回调地址",
    "has_secret": true/false
  }
}
```

---

### 7. 为特定claim注册回调
**POST** `/registerCallback`

#### 请求体
```json
{
  "claim": "UUID",
  "callback_url": "回调地址",
  "secret_key": "密钥（可选）"
}
```

#### 响应体 - 成功 (200)
```json
{
  "status": 200,
  "message": "Callback registered successfully",
  "data": {
    "claim": "UUID",
    "callback_url": "回调地址",
    "has_secret": true/false
  }
}
```

---

### 8. 查询回调状态
**GET** `/callbackStatus/<claim_uuid>`

#### 响应体示例
```json
{
  "status": 200,
  "message": "OK",
  "data": {
    "claim": "UUID",
    "callback_url": "回调地址",
    "status": "pending/success/failed",
    "last_attempt": "最后尝试时间",
    "attempt_count": 尝试次数
  }
}
```

---

### 9. 获取回调统计信息
**GET** `/callbackStatistics`

#### 响应体示例
```json
{
  "status": 200,
  "message": "OK",
  "data": {
    "total_callbacks": 10,
    "successful_callbacks": 8,
    "failed_callbacks": 2,
    "pending_callbacks": 0,
    "global_callback_url": "全局回调地址",
    "has_global_secret": true/false
  }
}
```

---

### 10. 清除特定claim回调配置
**POST** `/clearCallback/<claim_uuid>`

#### 响应体 - 成功 (200)
```json
{
  "status": 200,
  "message": "Callback cleared successfully",
  "data": {
    "claim": "UUID"
  }
}
```

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |

---

## 注意事项

1. **UUID格式**: 所有claim参数必须是有效的UUID格式
2. **批量限制**: 批量操作最多支持100个claim
3. **编码**: 所有接口支持UTF-8编码，中文不会乱码
4. **回调机制**: 
   - 可以设置全局回调（对所有claim生效）
   - 可以为单个claim设置特定回调
   - 回调会覆盖全局设置
5. **异步处理**: 
   - 验证过程是异步的
   - 返回的`task_id`可用于查询处理进度
   - 可以使用回调接收完成通知

---

## 示例调用

### 提交验证请求
```bash
curl -X POST http://139.224.18.139:5000/doVeritas \
  -H "Content-Type: application/json" \
  -d '{
    "title": "某地发生重大事件",
    "url": "https://example.com/news",
    "callback_url": "https://your-server.com/callback"
  }'
```

### 查询结果
```bash
curl "http://139.224.18.139:5000/queryVeritas?claim=123e4567-e89b-12d3-a456-426614174000"
```

### 批量重新验证
```bash
curl -X POST http://139.224.18.139:5000/batchRedoVeritas \
  -H "Content-Type: application/json" \
  -d '{
    "claims": [
      "uuid1",
      "uuid2",
      "uuid3"
    ]
  }'
```