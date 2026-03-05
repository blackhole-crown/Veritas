# 回调机制配置文件说明

## 文件结构
logs/callbacks/
├── config.json      # 回调配置
├── status.json      # 回调状态和历史记录
└── README.md        # 本文件

## 配置说明

### 1. config.json
```json
{
    "global_callback_url": "https://your-server.com/callback",  // 全局回调地址
    "global_secret_key": "your-secret-key",  // 全局签名密钥（可选）
    "callbacks": {  // 特定claim的回调配置
        "claim-uuid-1": {
            "url": "https://specific-server.com/callback1",
            "secret": "specific-secret1",
            "created_at": "2024-12-05T12:30:00Z"
        }
    },
    "retry_policy": {  // 重试策略
        "max_attempts": 3,
        "retry_delays": [5, 30, 120],
        "timeout": 30
    }
}