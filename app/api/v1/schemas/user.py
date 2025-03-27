from typing import Optional

from pydantic import EmailStr, Field

from .base import BaseSchema, DateTimeModelMixin, IDModelMixin


class UserCreate(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserInDBBase(IDModelMixin, DateTimeModelMixin, BaseSchema):
    username: str
    email: EmailStr
    is_active: bool = True


class UserRead(UserInDBBase):
    pass  # Excludes password


class UserInDB(UserInDBBase):
    hashed_password: str
