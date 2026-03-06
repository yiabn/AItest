# run.py
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

import uvicorn
from loguru import logger

if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    logger.info("启动游戏知识库后端服务...")
    logger.info(f"Python路径: {sys.path}")
    logger.info(f"项目根目录: {project_root}")
    
    uvicorn.run(
        "app.main:app",  # 使用字符串导入
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )