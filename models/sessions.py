from __future__ import annotations
from datetime import datetime
from models.Enums import class_names
from models.base import BaseDataModel
from schemas.models import SessionDB, SessionOut, SessionPatch


class SessionsModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection_name = class_names.SESSIONS.value
        self.collection = self.db_client[self.collection_name]

    async def insert_session(self, session: SessionDB) -> None:
        await self.collection.insert_one(session.model_dump())

    async def get_session_internal(self, session_id: str) -> SessionDB | None:
        doc = await self.collection.find_one({"session_id": session_id}, {"_id": 0})
        return SessionDB.model_validate(doc) if doc else None

    async def get_session_public(self, session_id: str) -> SessionOut | None:
        doc = await self.collection.find_one({"session_id": session_id}, {"_id": 0})
        return SessionOut.model_validate(doc) if doc else None

    async def list_sessions(self, *, limit: int | None = None) -> list[SessionOut]:
        cursor = self.collection.find({}, {"_id": 0}).sort("updated_at", -1)
        if limit is not None:
            cursor = cursor.limit(limit)
        docs = [doc async for doc in cursor]
        return [SessionOut.model_validate(doc) for doc in docs]

    async def update_session(self, session_id: str, patch: SessionPatch) -> None:
        fields = patch.model_dump(exclude_unset=True)
        if not fields:
            return
        await self.collection.update_one({"session_id": session_id}, {"$set": fields})

    async def touch(self, session_id: str, *, updated_at: datetime) -> None:
        await self.update_session(session_id, SessionPatch(updated_at=updated_at))

    async def update_session_csv(
        self,
        session_id: str,
        *,
        csv_filename: str,
        csv_path: str,
        updated_at: datetime,
    ) -> SessionOut | None:
        await self.update_session(
            session_id,
            SessionPatch(csv_filename=csv_filename, csv_path=csv_path, updated_at=updated_at),
        )
        return await self.get_session_public(session_id)

    async def delete_session(self, session_id: str) -> None:
        await self.collection.delete_one({"session_id": session_id})
