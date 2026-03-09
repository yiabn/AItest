# app/api/analyze.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.request import AnalyzeRequest
from app.models.response import AnalyzeResponse
from app.services.analysis_service import analysis_service
import uuid

router = APIRouter()

task_results = {}

@router.post("/url", response_model=dict)
async def analyze_url(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """提交分析任务，立即返回任务 ID"""
    task_id = str(uuid.uuid4())
    task_results[task_id] = {"status": "pending", "result": None}
    # 将耗时任务加入后台
    background_tasks.add_task(
        analysis_service.analyze_url_async,
        request.url,
        request.depth,
        request.include_raw,
        task_id,
        save_task_result
    )
    return {"task_id": task_id, "status": "pending"}

@router.get("/task/{task_id}", response_model=AnalyzeResponse)
async def get_task_result(task_id: str):
    """获取任务结果"""
    task = task_results.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task["status"] == "pending":
        raise HTTPException(status_code=202, detail="任务正在处理中")
    if task["status"] == "failed":
        raise HTTPException(status_code=500, detail=task.get("error", "处理失败"))
    return task["result"]

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

async def save_task_result(task_id: str, result, error):
    if error:
        task_results[task_id] = {"status": "failed", "error": str(error)}
    else:
        task_results[task_id] = {"status": "completed", "result": result}