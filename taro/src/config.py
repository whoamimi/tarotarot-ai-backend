# FastAPI App's Setting configurations

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    llm_id: str
    local_host_url: str
    supabase_key: str
    supabase_url: str
    db_user: str
    db_session: str
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    return Settings()

