from beanie import Document, Update, Save, SaveChanges, Replace, Insert, before_event
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from typing import Any, List

def get_utc_now():
    return datetime.now(timezone.utc)

class BaseDocument(Document):
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    @before_event(Insert)
    def set_created_at(self) -> None:
        self.created_at = get_utc_now()

    @before_event(Update, Save, SaveChanges, Replace)
    def set_updated_at(self) -> None:
        self.updated_at = get_utc_now()

class Convo(BaseDocument):
    conversation: str
    is_user: bool

class Session(BaseDocument):
    user_id: str
    conversations: List[Convo] = []

    class Settings:
        name = "sessions"