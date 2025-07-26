from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost/sales_agent_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Telegram
    telegram_bot_token: str = ""
    
    # Mercado Pago
    mercadopago_access_token: str = ""
    
    # LLM APIs
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # API
    api_v1_str: str = "/api/v1"
    project_name: str = "Sales Agent for Restaurants"
    
    class Config:
        env_file = ".env"


settings = Settings()