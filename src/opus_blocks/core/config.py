from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Modern Pydantic V2 configuration
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OpusBlocks API"
    app_version: str = "0.1.0"
    environment: str = "local"

    database_url: str = "postgresql+asyncpg://opus:opus@localhost:5432/opus_blocks"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""


settings = Settings()
