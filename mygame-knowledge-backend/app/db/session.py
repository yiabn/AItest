# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 数据库配置（根据你的PostgreSQL修改）
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/mygame_knowledge"

# 创建引擎
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 获取数据库会话（FastAPI依赖注入用）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 直接获取会话（非依赖注入场景）
db_session = SessionLocal()