"""CSV Data Science Agent – entry point.

Run:  uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

import os

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from helpers.config import get_settings
from routers import chat, sessions


settings = get_settings()


async def startup_span(app: FastAPI) -> None:
    config = get_settings()
    app.mongodb_conn = AsyncIOMotorClient(config.MONGODB_URL)
    app.mongodb = app.mongodb_conn[config.MONGODB_DB_NAME]


async def shutdown_span(app: FastAPI) -> None:
    # Close Mongo connection.
    if getattr(app, "mongodb_conn", None) is not None:
        app.mongodb_conn.close()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Upload a CSV file, then ask questions in plain English. "
        "The LangGraph agent writes and runs pandas/matplotlib code "
        "and returns text answers + charts."
    ),
    version="1.0.0",
)


@app.on_event("startup")
async def on_startup() -> None:
    await startup_span(app)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await shutdown_span(app)

app.include_router(sessions.router)
app.include_router(chat.router)


@app.get("/", tags=["welcome"])
async def welcome():
    return {
        "message": "Welcome to the CSV Agent API",
        "app": settings.APP_NAME,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/debug/tracing", tags=["debug"])
async def debug_tracing():
    """Show whether LangSmith tracing is enabled (no secrets)."""
    tracing = (os.getenv("LANGCHAIN_TRACING_V2") or "").lower() in {"1", "true", "yes", "on"}
    project = os.getenv("LANGCHAIN_PROJECT")
    endpoint = os.getenv("LANGCHAIN_ENDPOINT")
    has_api_key = bool(os.getenv("LANGCHAIN_API_KEY"))

    smith_tracing = (os.getenv("LANGSMITH_TRACING") or "").lower() in {"1", "true", "yes", "on"}
    smith_project = os.getenv("LANGSMITH_PROJECT")
    smith_endpoint = os.getenv("LANGSMITH_ENDPOINT")
    smith_has_api_key = bool(os.getenv("LANGSMITH_API_KEY"))
    return {
        "langsmith_tracing_v2": tracing,
        "langsmith_project": project,
        "langsmith_endpoint": endpoint,
        "langsmith_api_key_present": has_api_key,
        "langsmith_tracing": smith_tracing,
        "langsmith_project_alt": smith_project,
        "langsmith_endpoint_alt": smith_endpoint,
        "langsmith_api_key_present_alt": smith_has_api_key,
    }
