from __future__ import annotations
from .Enums import class_names
from models.base import BaseDataModel
from schemas.models import MessageDB, MessageOut


class MessagesModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection_name = class_names.MESSAGES.value
        self.collection = self.db_client[self.collection_name]

    async def insert_message(self, message: MessageDB) -> None:
        await self.collection.insert_one(message.model_dump())

    async def list_messages(self, session_id: str) -> list[MessageOut]:
        cursor = (
            self.collection.find({"session_id": session_id}, {"_id": 0}).sort("created_at", 1)
        )
        docs = [doc async for doc in cursor]
        return [MessageOut.model_validate(doc) for doc in docs]

    async def delete_messages_for_session(self, session_id: str) -> None:
        await self.collection.delete_many({"session_id": session_id})
