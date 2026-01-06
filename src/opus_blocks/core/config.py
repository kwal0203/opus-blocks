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
    llm_use_openai: bool = False

    embeddings_provider: str = "stub"
    embeddings_model: str = "text-embedding-3-small"
    embeddings_use_openai: bool = False

    vector_backend: str = "stub"
    vector_collection: str = "opus_blocks_facts"
    vector_persist_path: str = "storage/vector"

    rate_limit_enabled: bool = False
    rate_limit_storage_uri: str = "redis://localhost:6379/3"
    rate_limit_auth: str = "20/minute"
    rate_limit_upload: str = "30/minute"
    rate_limit_job: str = "30/minute"


settings = Settings()
