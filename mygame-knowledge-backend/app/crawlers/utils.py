# app/crawlers/utils.py
import random
import time
from typing import Optional

def random_delay(min_delay: float = 1.0, max_delay: float = 3.0):
    """随机延迟"""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

def extract_domain(url: str) -> Optional[str]:
    """提取域名"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return None

def is_same_domain(url1: str, url2: str) -> bool:
    """判断是否同一域名"""
    domain1 = extract_domain(url1)
    domain2 = extract_domain(url2)
    return domain1 == domain2