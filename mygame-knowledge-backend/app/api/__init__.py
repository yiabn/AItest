# app/api/__init__.py
"""API路由模块"""

from . import analyze
from . import chat

# 直接导出 router 以便导入
from .analyze import router as analyze_router
from .chat import router as chat_router

__all__ = ['analyze', 'chat', 'analyze_router', 'chat_router']