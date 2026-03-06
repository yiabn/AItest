# app/crawlers/__init__.py
"""
爬虫模块
"""
from .base import BaseCrawler
from .m99_crawler import M99Crawler

__all__ = ['BaseCrawler', 'M99Crawler']