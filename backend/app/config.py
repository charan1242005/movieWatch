from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite:///./moviewatch.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    email_host: str = ""
    email_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from: str = "noreply@moviewatch.local"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    default_check_interval_minutes: int = 5
    mock_provider_availability_delay_seconds: int = 60

    cors_origins: str = "http://localhost:4200"

    class Config:
        env_file = ".env"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
