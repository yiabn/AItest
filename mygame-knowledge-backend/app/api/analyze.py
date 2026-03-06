# app/api/analyze.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio

from app.models.request import AnalyzeRequest
from app.models.response import AnalyzeResponse
from app.services.analysis_service import AnalysisService

router = APIRouter()
service = AnalysisService()

@router.post("/url", response_model=AnalyzeResponse)
async def analyze_url(request: AnalyzeRequest):
    """分析指定URL"""
    try:
        result = await service.analyze_url(
            url=request.url,
            depth=request.depth,
            include_raw=request.include_raw
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}", response_model=AnalyzeResponse)
async def get_task(task_id: str):
    """获取分析任务结果"""
    result = service.get_task(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="任务不存在")
    return result

@router.get("/types")
async def get_page_types():
    """获取支持的页面类型"""
    return {
        "types": [
            {"value": "pet", "label": "幻兽"},
            {"value": "equipment", "label": "装备"},
            {"value": "skill", "label": "技能"},
            {"value": "dungeon", "label": "副本"},
            {"value": "map", "label": "地图"},
            {"value": "general", "label": "通用"}
        ]
    }