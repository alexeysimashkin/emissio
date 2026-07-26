from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # База данных
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # MAX (мессенджер)
    MAX_BOT_TOKEN: str = "not_set_yet"
    MAX_WEBHOOK_URL: str = "https://example.com/webhook"
    MAX_API_URL: str = "https://api.max.ru/v1"
    
    # Админ
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_FULL_NAME: str
    
    # Настройки приложения
    APP_NAME: str = "ЕМИССиО"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
