"""
Chat endpoint
POST /sessions/{session_id}/chat     → ask a question, get answer + optional chart
GET  /sessions/{session_id}/history  → full message history
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage, AIMessage

from schemas.models import ChatRequest, ChatResponse, MessageDB, MessageOut, HistoryResponse
from models.messages import MessagesModel
from models.sessions import SessionsModel
from agents.graph import csv_agent

router = APIRouter(prefix="/sessions", tags=["chat"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

async def _load_history(db, session_id: str) -> list:
    docs = await MessagesModel(db_client=db).list_messages(session_id)
    history = []
    for msg in docs:
        if msg.role == "user":
            history.append(HumanMessage(content=msg.content))
        else:
            history.append(AIMessage(content=msg.content))
    return history


@router.post("/{session_id}/chat", response_model=ChatResponse)
async def chat(session_id: str, body: ChatRequest, request: Request):
    sessions_model = SessionsModel(request.app.mongodb)
    messages_model = MessagesModel(request.app.mongodb)
    session = await sessions_model.get_session_internal(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.csv_path:
        raise HTTPException(
            status_code=400,
            detail="No CSV uploaded yet. POST /sessions/{id}/upload first."
        )

    history = await _load_history(request.app.mongodb, session_id)

    initial_state = {
        "messages": history + [HumanMessage(content=body.query)],
        "session_id": session_id,
        "csv_path": session.csv_path,
        "csv_info": "",
        "generated_code": None,
        "code_output": None,
        "chart_b64": None,
        "exec_error": None,
    }

    final_state = await csv_agent.ainvoke(initial_state)

    # The last AIMessage is the final answer
    last_ai = next(
        (m for m in reversed(final_state["messages"]) if isinstance(m, AIMessage)),
        None,
    )
    answer = last_ai.content if last_ai else "No answer generated."
    code      = final_state.get("generated_code")
    output    = final_state.get("code_output")
    chart_b64 = final_state.get("chart_b64")

    now = utc_now()
    message_id = str(uuid.uuid4())

    await messages_model.insert_message(
        MessageDB(
            session_id=session_id,
            role="user",
            content=body.query,
            code=None,
            chart=None,
            created_at=now,
            message_id=None,
        )
    )
    await messages_model.insert_message(
        MessageDB(
            session_id=session_id,
            role="assistant",
            content=answer,
            code=code,
            chart=chart_b64,
            created_at=now,
            message_id=message_id,
        )
    )
    await sessions_model.touch(session_id, updated_at=now)

    return ChatResponse(
        answer=answer,
    )


@router.get("/{session_id}/history", response_model=HistoryResponse)
async def get_history(session_id: str, request: Request):
    sessions_model = SessionsModel(request.app.mongodb)
    if not await sessions_model.get_session_internal(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await MessagesModel(request.app.mongodb).list_messages(session_id)
    return HistoryResponse(session_id=session_id, messages=messages)
