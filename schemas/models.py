from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


# ── Session ────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    title: str | None = None

class SessionOut(BaseModel):
    session_id: str
    title: str | None
    csv_filename: str | None       # original uploaded file name
    created_at: datetime
    updated_at: datetime


class SessionDB(SessionOut):
    # Internal field used by the agent and delete endpoint.
    csv_path: str | None = None


class SessionPatch(BaseModel):
    title: str | None = None
    csv_filename: str | None = None
    csv_path: str | None = None
    updated_at: datetime | None = None


# ── Chat ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Plain-English question about the CSV")

class ChatResponse(BaseModel):
    answer: str                    # LLM final text answer

# ── History ────────────────────────────────────────────────────────────────

class MessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    code: str | None = None
    chart: str | None = None
    created_at: datetime


class MessageDB(MessageOut):
    session_id: str
    message_id: str | None = None

class HistoryResponse(BaseModel):
    session_id: str
    messages: list[MessageOut]
