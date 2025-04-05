from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Shared properties"""

    email: EmailStr


class UserCreate(UserBase):
    """Properties to receive via API on creation"""

    password: str


class UserUpdate(UserBase):
    """Properties to receive via API on update (optional)"""

    password: Optional[str] = None


class UserInDBBase(UserBase):
    """Properties stored in DB"""

    id: int
    is_active: bool

    class Config:
        from_attributes = True


class User(UserInDBBase):
    """Additional properties to return via API"""

    pass


class UserInDB(UserInDBBase):
    """Additional properties stored in DB"""

    hashed_password: str
