import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── LLM ──────────────────────────────────────────────────
    OPENAI_API_KEY: str
    # OpenAI-compatible base URL (set this for OpenRouter, etc.)
    OPENAI_BASE_URL: str | None = None
    LLM_MODEL: str = "gpt-4o"

    # Optional OpenRouter identification headers
    OPENROUTER_SITE_URL: str | None = None
    OPENROUTER_APP_NAME: str | None = None

    # ── MongoDB ───────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "csv_agent_db"

    # ── File storage ──────────────────────────────────────────
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_CSV_ROWS: int = 50_000

    # LangSmith tracing (optional)
    # Keeping these fields allows .env to include LANGCHAIN_* without errors,
    # and lets us sync them into os.environ for local uvicorn runs.
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str | None = None


    # ── App ───────────────────────────────────────────────────
    APP_NAME: str = "CSV Data Science Agent"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def ensure_upload_dir(self) -> None:
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def llm_default_headers(self) -> dict[str, str] | None:
        headers: dict[str, str] = {}
        if self.OPENROUTER_SITE_URL:
            headers["HTTP-Referer"] = self.OPENROUTER_SITE_URL
        if self.OPENROUTER_APP_NAME:
            headers["X-Title"] = self.OPENROUTER_APP_NAME
        return headers or None


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # If values were loaded from `.env` by pydantic-settings (local uvicorn),
    # sync them into os.environ so LangChain/LangSmith tracing can see them.
    if s.langchain_api_key:
        os.environ.setdefault("LANGCHAIN_API_KEY", s.langchain_api_key)
        os.environ.setdefault("LANGSMITH_API_KEY", s.langchain_api_key)

    if s.langchain_project:
        os.environ.setdefault("LANGCHAIN_PROJECT", s.langchain_project)
        os.environ.setdefault("LANGSMITH_PROJECT", s.langchain_project)

    if s.langchain_tracing_v2:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        # Some versions/tools also look for LANGSMITH_TRACING
        os.environ.setdefault("LANGSMITH_TRACING", "true")

    s.ensure_upload_dir()
    return s
