from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field

PRIORITY_MAP = {1: "High", 2: "Medium", 3: "Low"}
VALID_PRIORITIES = list(PRIORITY_MAP.keys())


class TodoBase(BaseModel):
    """Shared properties"""

    title: str
    description: Optional[str] = None
    status: str = "Not Started"
    due_date: Optional[date] = None
    priority: int = Field(default=2, ge=min(VALID_PRIORITIES), le=max(VALID_PRIORITIES))


class TodoCreate(TodoBase):
    """Properties to receive on item creation"""

    pass


class TodoUpdate(BaseModel):
    """Properties to receive on item update"""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[int] = Field(
        default=None, ge=min(VALID_PRIORITIES), le=max(VALID_PRIORITIES)
    )


class TodoInDBBase(TodoBase):
    """Properties stored in DB"""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    photo_filename: Optional[str] = None

    due_date: Optional[date]
    priority: int

    class Config:
        from_attributes = True


class Todo(TodoInDBBase):
    """Properties to return to client"""

    @property
    def priority_str(self) -> str:
        return PRIORITY_MAP.get(self.priority, "Unknown")
