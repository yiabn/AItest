# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from loguru import logger
import sys
import os
from app.database import db

# 导入路由
from app.api import knowledge  # 添加 knowledge
from app.api.analyze import router as analyze_router
from app.api.chat import router as chat_router
from app.config import settings

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

app = FastAPI(
    title="游戏知识库 API",
    description="魔域游戏资料抓取与分析系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(analyze_router, prefix="/api/analyze", tags=["分析"])
app.include_router(chat_router, prefix="/api/chat", tags=["对话"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])  # 新增

# 打印所有注册的路由
logger.info("=" * 50)
logger.info("已注册的路由:")
for route in app.routes:
    if hasattr(route, "methods"):
        logger.info(f"{route.methods} {route.path}")
logger.info("=" * 50)

@app.get("/")
async def root():
    return {"message": "游戏知识库 API 服务", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/info")
async def app_info():
    return {
        "app_name": settings.APP_NAME,
        "debug": settings.DEBUG,
        "version": "1.0.0"
    }

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库连接"""
    try:
        await db.connect()
        logger.info("数据库连接已初始化")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        # 根据需求决定是否抛出异常

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时关闭数据库连接"""
    await db.close()
    logger.info("数据库连接已关闭")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)