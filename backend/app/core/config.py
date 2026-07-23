from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    MAX_BOT_TOKEN: str
    MAX_WEBHOOK_URL: str
    MAX_API_URL: str = "https://api.max.ru/v1"
    
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_FULL_NAME: str
    
    APP_NAME: str = "ЕМИССиО"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
