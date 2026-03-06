# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "游戏知识库"
    DEBUG: bool = True
    
    # PostgreSQL 配置
    DB_HOST: str = Field("localhost", validation_alias="DB_HOST")
    DB_PORT: int = Field(5432, validation_alias="DB_PORT")
    DB_NAME: str = Field("mygame_knowledge", validation_alias="DB_NAME")
    DB_USER: str = Field("postgres", validation_alias="DB_USER")
    DB_PASSWORD: str = Field("postgres", validation_alias="DB_PASSWORD")  # 默认为空
    DB_POOL_MIN_SIZE: int = Field(5, validation_alias="DB_POOL_MIN_SIZE")
    DB_POOL_MAX_SIZE: int = Field(20, validation_alias="DB_POOL_MAX_SIZE")
    
    # 爬虫配置
    REQUEST_TIMEOUT: int = Field(30, validation_alias="REQUEST_TIMEOUT")
    REQUEST_DELAY: float = Field(1.0, validation_alias="REQUEST_DELAY")
    MAX_RETRIES: int = Field(3, validation_alias="MAX_RETRIES")
    
    USER_AGENT: str = Field(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        validation_alias="USER_AGENT"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 忽略多余的字段

# 创建配置实例
try:
    settings = Settings()
    print(f"✅ 配置加载成功: DB={settings.DB_NAME}@{settings.DB_HOST}:{settings.DB_PORT}")
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    print("使用默认配置...")
    settings = Settings(
        DB_PASSWORD="",  # 手动设置空密码
    )