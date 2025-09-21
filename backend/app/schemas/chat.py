# backend/app/schemas/chat.py
from pydantic import BaseModel, Field, BeforeValidator
from typing import List, Annotated, Literal
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class ChatMessage(BaseModel):
    sender: Literal["user", "agent", "human"]
    text: str
    timestamp: datetime

class Chat(BaseModel):
    id: PyObjectId = Field(alias="_id")
    session_id: str
    user_id: str | None = None # Optional field for when you add login
    messages: List[ChatMessage]
    status: Literal["open", "closed", "escalated"]
    created_at: datetime