from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TodoBase(BaseModel):
    """Shared properties"""

    title: str
    description: Optional[str] = None
    status: str = "Not Started"


class TodoCreate(TodoBase):
    """Properties to receive on item creation"""

    pass


class TodoUpdate(BaseModel):
    """Properties to receive on item update"""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class TodoInDBBase(TodoBase):
    """Properties stored in DB"""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    photo_filename: Optional[str] = None

    class Config:
        from_attributes = True


class Todo(TodoInDBBase):
    """Properties to return to client"""

    pass
