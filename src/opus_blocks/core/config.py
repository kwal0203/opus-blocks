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
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_exp_minutes: int = 60
    storage_root: str = "storage"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_prompt_version: str = "v1"


settings = Settings()
