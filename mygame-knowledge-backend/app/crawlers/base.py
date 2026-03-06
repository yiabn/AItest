import requests
from typing import Optional, Dict, Any
from time import sleep
import random
from loguru import logger
from app.config import settings

class BaseCrawler:
    """基础爬虫类"""
    
    def __init__(self, delay: float = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.delay = delay or settings.REQUEST_DELAY
        
    def fetch(self, url: str, retry: int = None) -> Optional[str]:
        """获取页面内容"""
        retry = retry or settings.MAX_RETRIES
        
        for i in range(retry):
            try:
                logger.info(f"正在抓取: {url}")
                response = self.session.get(
                    url, 
                    timeout=settings.REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # 检查编码
                if response.encoding:
                    response.encoding = response.apparent_encoding or 'utf-8'
                
                logger.success(f"抓取成功: {url} - 大小: {len(response.text)} 字节")
                return response.text
                
            except requests.RequestException as e:
                logger.error(f"抓取失败 {url}: {e}")
                if i < retry - 1:
                    wait_time = 2 ** i + random.uniform(0, 1)
                    logger.info(f"等待 {wait_time:.2f} 秒后重试...")
                    sleep(wait_time)
                else:
                    logger.error(f"达到最大重试次数，放弃抓取: {url}")
                    return None
                    
    def fetch_json(self, url: str, params: Dict = None) -> Optional[Dict]:
        """获取JSON数据"""
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取JSON失败 {url}: {e}")
            return None
            
    def post_json(self, url: str, data: Dict = None) -> Optional[Dict]:
        """POST JSON数据"""
        try:
            response = self.session.post(
                url,
                json=data,
                timeout=settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"POST JSON失败 {url}: {e}")
            return None
            
    def _respect_rate_limit(self):
        """遵守请求频率限制"""
        if self.delay > 0:
            sleep(self.delay + random.uniform(0, 0.5))