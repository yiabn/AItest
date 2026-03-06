# app/models/__init__.py
"""
数据模型模块
"""
from .request import AnalyzeRequest, ChatRequest
from .response import AnalyzeResponse, EntityInfo, RelationInfo, ChatResponse

__all__ = [
    'AnalyzeRequest', 'ChatRequest',
    'AnalyzeResponse', 'EntityInfo', 'RelationInfo', 'ChatResponse'
]