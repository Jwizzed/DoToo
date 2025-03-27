from typing import Optional

from pydantic import Field

from app.db.models.todo import TodoStatus
from .base import BaseSchema, DateTimeModelMixin, IDModelMixin


class TodoCreate(BaseSchema):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    # image_url is handled separately during upload if implemented fully
    # status: Optional[TodoStatus] = TodoStatus.PENDING # Default handled by model/db


class TodoUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[TodoStatus] = None
    # image_url: Optional[str] = None


class TodoInDBBase(IDModelMixin, DateTimeModelMixin, BaseSchema):
    title: str
    description: Optional[str] = None
    status: TodoStatus
    owner_id: int
    image_url: Optional[str] = None


class TodoRead(TodoInDBBase):
    pass


class TodoInDB(TodoInDBBase):
    pass
