from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized runtime settings."""
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    use_pgvector: bool = Field(default=True, validation_alias="USE_PGVECTOR")
    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    groq_model: str | None = Field(default=None, validation_alias="GROQ_MODEL")

    class Config:
        env_file = "env.local"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    print("✅ DEBUG Settings loaded:", settings.model_dump())
    return settings
