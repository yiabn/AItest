# app/utils/helpers.py
import hashlib
import json
from typing import Any, Dict
from datetime import datetime

def generate_id(prefix: str = "") -> str:
    """生成唯一ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    hash_input = f"{prefix}{timestamp}".encode()
    return hashlib.md5(hash_input).hexdigest()[:16]

def safe_json_loads(data: str) -> Dict[str, Any]:
    """安全加载JSON"""
    try:
        return json.loads(data)
    except:
        return {}

def truncate_text(text: str, max_length: int = 1000) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."