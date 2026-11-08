from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://docqa:docqa@localhost:5432/docqa"
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5-5"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384  # must match the model above

    top_k: int = 5
    min_score: float = 0.40  # cosine similarity floor; below this we refuse

    chunk_max_chars: int = 1500
    chunk_overlap_chars: int = 200
    data_dir: str = "data/raw"


settings = Settings()
