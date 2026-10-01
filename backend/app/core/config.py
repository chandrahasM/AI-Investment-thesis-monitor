from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    EXA_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./signal.db"
    DEMO_MODE: bool = False
    OPENAI_API_KEY: Optional[str] = None

    @property
    def is_demo_mode(self) -> bool:
        return self.DEMO_MODE or not self.EXA_API_KEY

    @property
    def exa_available(self) -> bool:
        return bool(self.EXA_API_KEY) and not self.DEMO_MODE


settings = Settings()
