from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.user import UserCreate
from app.db.models import User


class UserRepository:
    """
    Handles database operations for User model.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Fetches a user by their ID."""
        result = await self.db.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Fetches a user by their username."""
        result = await self.db.execute(select(User).filter(User.username == username))
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Fetches a user by their email."""
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def create_user(self, user_in: UserCreate, hashed_password: str) -> User:
        """Creates a new user in the database."""
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            is_active=True
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
