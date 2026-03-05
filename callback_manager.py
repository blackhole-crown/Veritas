"""
回调管理器 - 负责管理Webhook回调的发送和状态跟踪
不修改数据库，使用本地JSON文件存储配置和日志
"""
import json
import os
import time
import threading
import requests
import hmac
import hashlib
from datetime import datetime
from typing import Optional, Dict, List
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class CallbackManager:
    """回调管理器单例类"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 基本配置
        self.base_dir = os.path.join(os.path.dirname(__file__), 'logs')
        self.callback_dir = os.path.join(self.base_dir, 'callbacks')
        
        # 确保目录存在
        os.makedirs(self.callback_dir, exist_ok=True)
        
        # 配置文件路径
        self.config_file = os.path.join(self.callback_dir, 'config.json')
        self.status_file = os.path.join(self.callback_dir, 'status.json')
        
        # 加载配置
        self.config = self._load_config()
        self.status_data = self._load_status()
        
        # 内存缓存（提高性能）
        self.callback_cache = {}  # claim_uuid -> callback_url
        self.status_cache = {}    # claim_uuid -> 最新状态
        
        self._initialized = True
        logger.info(f"CallbackManager initialized, config directory: {self.callback_dir}")
    
    def _load_config(self) -> Dict:
        """加载回调配置文件"""
        default_config = {
            "global_callback_url": None,
            "global_secret_key": None,
            "callbacks": {},  # claim_uuid -> {url, secret, created_at}
            "retry_policy": {
                "max_attempts": 3,
                "retry_delays": [5, 30, 120],  # 重试延迟（秒）
                "timeout": 30  # 请求超时（秒）
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
        
        # 保存默认配置
        self._save_config(default_config)
        return default_config
    
    def _load_status(self) -> Dict:
        """加载回调状态文件"""
        default_status = {
            "callbacks": {},  # claim_uuid -> [status_history]
            "statistics": {
                "total_sent": 0,
                "total_failed": 0,
                "total_success": 0
            }
        }
        
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load status file: {e}")
        
        return default_status
    
    def _save_config(self, config: Optional[Dict] = None):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config or self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")
    
    def _save_status(self, status: Optional[Dict] = None):
        """保存状态到文件"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status or self.status_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save status file: {e}")
    
    def set_global_callback(self, url: str, secret_key: Optional[str] = None) -> bool:
        """设置全局回调配置"""
        try:
            self.config["global_callback_url"] = url
            if secret_key:
                self.config["global_secret_key"] = secret_key
            self._save_config()
            logger.info(f"Global callback set: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to set global callback: {e}")
            return False
    
    def register_callback(self, claim_uuid: str, callback_url: str, 
                         secret_key: Optional[str] = None) -> bool:
        """为特定claim注册回调"""
        try:
            # 验证UUID格式
            UUID(claim_uuid)
            
            self.config["callbacks"][claim_uuid] = {
                "url": callback_url,
                "secret": secret_key,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # 更新内存缓存
            self.callback_cache[claim_uuid] = callback_url
            
            self._save_config()
            logger.info(f"Callback registered for claim {claim_uuid}: {callback_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to register callback: {e}")
            return False
    
    def get_callback_url(self, claim_uuid: str) -> Optional[str]:
        """获取claim对应的回调URL"""
        # 检查内存缓存
        if claim_uuid in self.callback_cache:
            return self.callback_cache[claim_uuid]
        
        # 检查配置文件
        callback_info = self.config["callbacks"].get(claim_uuid)
        if callback_info:
            url = callback_info.get("url")
            self.callback_cache[claim_uuid] = url
            return url
        
        # 返回全局回调
        return self.config.get("global_callback_url")
    
    def get_callback_secret(self, claim_uuid: str) -> Optional[str]:
        """获取claim对应的签名密钥"""
        callback_info = self.config["callbacks"].get(claim_uuid)
        if callback_info:
            return callback_info.get("secret")
        
        return self.config.get("global_secret_key")
    
    def _generate_signature(self, payload: Dict, secret: str) -> str:
        """生成HMAC签名"""
        # 对payload进行排序以确保一致性
        sorted_payload = json.dumps(payload, sort_keys=True)
        message = sorted_payload.encode('utf-8')
        secret_bytes = secret.encode('utf-8')
        
        return hmac.new(secret_bytes, message, hashlib.sha256).hexdigest()
    
    def _create_callback_payload(self, claim_uuid: str, task_id: str, 
                                status: str, title: Optional[str] = None) -> Dict:
        """创建回调数据"""
        payload = {
            "event": f"veritas.{status}",
            "claim": claim_uuid,
            "task_id": task_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if title:
            payload["title"] = title
        
        return payload
    
    def send_callback(self, claim_uuid: str, task_id: str, 
                     status: str, title: Optional[str] = None) -> bool:
        """
        发送回调通知（异步）
        返回：是否成功注册了回调（不代表发送成功）
        """
        callback_url = self.get_callback_url(claim_uuid)
        if not callback_url:
            logger.debug(f"No callback URL registered for claim {claim_uuid}")
            return False
        
        # 异步发送
        thread = threading.Thread(
            target=self._send_callback_async,
            args=(claim_uuid, task_id, status, title, callback_url),
            daemon=True
        )
        thread.start()
        
        return True
    
    def _send_callback_async(self, claim_uuid: str, task_id: str, status: str, 
                            title: Optional[str], callback_url: str):
        """异步发送回调的实际逻辑"""
        max_attempts = self.config["retry_policy"]["max_attempts"]
        retry_delays = self.config["retry_policy"]["retry_delays"]
        timeout = self.config["retry_policy"]["timeout"]
        
        # 创建payload
        payload = self._create_callback_payload(claim_uuid, task_id, status, title)
        
        # 添加签名
        secret = self.get_callback_secret(claim_uuid)
        if secret:
            payload["signature"] = self._generate_signature(payload, secret)
        
        # 记录开始状态
        self._record_callback_start(claim_uuid, callback_url, payload)
        
        # 重试发送
        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    callback_url,
                    json=payload,
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Veritas-Callback/1.0',
                        'Content-Type': 'application/json'
                    }
                )
                
                # 记录尝试
                self._record_callback_attempt(
                    claim_uuid, attempt + 1, 
                    status_code=response.status_code,
                    response_text=response.text[:500] if response.text else None
                )
                
                if response.status_code in [200, 201, 202]:
                    # 成功
                    self._record_callback_success(claim_uuid)
                    logger.info(f"Callback sent successfully for claim {claim_uuid}, attempt {attempt + 1}")
                    return True
                else:
                    logger.warning(f"Callback failed with status {response.status_code} for claim {claim_uuid}")
            
            except requests.exceptions.Timeout:
                self._record_callback_attempt(
                    claim_uuid, attempt + 1, 
                    error="Timeout"
                )
                logger.warning(f"Callback timeout for claim {claim_uuid}, attempt {attempt + 1}")
            
            except Exception as e:
                self._record_callback_attempt(
                    claim_uuid, attempt + 1, 
                    error=str(e)
                )
                logger.error(f"Callback error for claim {claim_uuid}, attempt {attempt + 1}: {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_attempts - 1:
                delay = retry_delays[attempt] if attempt < len(retry_delays) else retry_delays[-1]
                time.sleep(delay)
        
        # 所有尝试都失败
        self._record_callback_failure(claim_uuid)
        logger.error(f"All callback attempts failed for claim {claim_uuid}")
        return False
    
    def _record_callback_start(self, claim_uuid: str, callback_url: str, payload: Dict):
        """记录回调开始"""
        if claim_uuid not in self.status_data["callbacks"]:
            self.status_data["callbacks"][claim_uuid] = []
        
        history_entry = {
            "callback_url": callback_url,
            "payload": payload,
            "start_time": datetime.utcnow().isoformat(),
            "attempts": [],
            "final_status": "pending"
        }
        
        # 只保留最近5条记录
        self.status_data["callbacks"][claim_uuid].insert(0, history_entry)
        if len(self.status_data["callbacks"][claim_uuid]) > 5:
            self.status_data["callbacks"][claim_uuid] = self.status_data["callbacks"][claim_uuid][:5]
        
        self.status_data["statistics"]["total_sent"] += 1
        self._save_status()
    
    def _record_callback_attempt(self, claim_uuid: str, attempt_num: int, 
                               status_code: Optional[int] = None,
                               response_text: Optional[str] = None,
                               error: Optional[str] = None):
        """记录回调尝试"""
        if claim_uuid not in self.status_data["callbacks"]:
            return
        
        history = self.status_data["callbacks"][claim_uuid]
        if not history:
            return
        
        attempt_record = {
            "attempt": attempt_num,
            "time": datetime.utcnow().isoformat(),
        }
        
        if status_code is not None:
            attempt_record["status_code"] = status_code
            if response_text:
                attempt_record["response"] = response_text
        
        if error:
            attempt_record["error"] = error
        
        history[0]["attempts"].append(attempt_record)
        self._save_status()
    
    def _record_callback_success(self, claim_uuid: str):
        """记录回调成功"""
        if claim_uuid not in self.status_data["callbacks"]:
            return
        
        history = self.status_data["callbacks"][claim_uuid]
        if not history:
            return
        
        history[0]["final_status"] = "success"
        history[0]["end_time"] = datetime.utcnow().isoformat()
        self.status_data["statistics"]["total_success"] += 1
        self._save_status()
    
    def _record_callback_failure(self, claim_uuid: str):
        """记录回调失败"""
        if claim_uuid not in self.status_data["callbacks"]:
            return
        
        history = self.status_data["callbacks"][claim_uuid]
        if not history:
            return
        
        history[0]["final_status"] = "failed"
        history[0]["end_time"] = datetime.utcnow().isoformat()
        self.status_data["statistics"]["total_failed"] += 1
        self._save_status()
    
    def get_callback_status(self, claim_uuid: str) -> Dict:
        """获取回调状态"""
        if claim_uuid not in self.status_data["callbacks"]:
            return {"status": "not_registered"}
        
        history = self.status_data["callbacks"][claim_uuid]
        if not history:
            return {"status": "no_history"}
        
        latest = history[0]
        callback_url = latest.get("callback_url", "unknown")
        
        return {
            "status": latest.get("final_status", "unknown"),
            "callback_url": callback_url,
            "start_time": latest.get("start_time"),
            "end_time": latest.get("end_time"),
            "attempts": len(latest.get("attempts", [])),
            "last_attempt": latest.get("attempts", [])[-1] if latest.get("attempts") else None
        }
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return self.status_data.get("statistics", {})
    
    def clear_callback(self, claim_uuid: str) -> bool:
        """清除claim的回调配置"""
        try:
            if claim_uuid in self.config["callbacks"]:
                del self.config["callbacks"][claim_uuid]
                self._save_config()
            
            if claim_uuid in self.callback_cache:
                del self.callback_cache[claim_uuid]
            
            logger.info(f"Callback cleared for claim {claim_uuid}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear callback: {e}")
            return False


# 全局实例
callback_manager = CallbackManager()