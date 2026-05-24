"""
Session CRUD + CSV upload
POST   /sessions                     → create session
POST   /sessions/{id}/upload         → upload CSV file (required before chatting)
GET    /sessions                     → list all sessions
GET    /sessions/{id}                → get one session
DELETE /sessions/{id}                → delete session + messages + CSV file
"""
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from schemas.models import CreateSessionRequest, SessionDB, SessionOut
from models.sessions import SessionsModel
from models.messages import MessagesModel
from helpers.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/sessions", tags=["sessions"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(body: CreateSessionRequest, request: Request):
    sessions_model = SessionsModel(request.app.mongodb)
    session_id = str(uuid.uuid4())
    now = utc_now()
    session = SessionDB(
        session_id=session_id,
        title=body.title,
        csv_filename=None,
        csv_path=None,
        created_at=now,
        updated_at=now,
    )
    await sessions_model.insert_session(session)
    return SessionOut.model_validate(session)


@router.post("/{session_id}/upload", response_model=SessionOut)
async def upload_csv(session_id: str, request: Request, file: UploadFile = File(...)):
    sessions_model = SessionsModel(request.app.mongodb)
    session = await sessions_model.get_session_internal(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    # Save to uploads/{session_id}.csv
    dest = settings.UPLOAD_DIR / f"{session_id}.csv"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    now = utc_now()
    
    updated = await sessions_model.update_session_csv(
        session_id,
        csv_filename=file.filename,
        csv_path=str(dest),
        updated_at=now,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated


@router.get("", response_model=list[SessionOut])
async def list_sessions(request: Request):
    return await SessionsModel(request.app.mongodb).list_sessions()


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: str, request: Request):
    session = await SessionsModel(request.app.mongodb).get_session_public(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str, request: Request):
    sessions_model = SessionsModel(request.app.mongodb)
    messages_model = MessagesModel(request.app.mongodb)
    session = await sessions_model.get_session_internal(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Remove CSV file
    if session.csv_path:
        Path(session.csv_path).unlink(missing_ok=True)

    await sessions_model.delete_session(session_id)
    await messages_model.delete_messages_for_session(session_id)
    return {"deleted": True, "session_id": session_id}
