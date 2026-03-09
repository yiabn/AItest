# app/db/session.py（基于你的代码，完善PostgreSQL配置）
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加载环境变量（建议用.env管理，避免硬编码）
load_dotenv()

# PostgreSQL连接配置（贴合你的代码体系）
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "123456")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "content_analysis")

# PostgreSQL连接字符串（psycopg2是PostgreSQL官方驱动）
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# 创建引擎（适配PostgreSQL，保留你的engine变量名）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 检查连接有效性
    echo=False  # 调试时设为True
)

# 创建会话（保留你的SessionLocal）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 依赖函数（供业务代码调用）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 兼容你原代码的全局会话
db_session = SessionLocal()