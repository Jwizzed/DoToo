from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, create_access_token
from app.crud import crud_user
from app.db.models import User
from app.schemas.user import UserCreate


class AuthService:
    async def register_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """Handles user registration business logic."""

        existing_user = await crud_user.get_user_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = await crud_user.create_user(db=db, user_in=user_in)
        return user

    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Handles user authentication business logic."""

        user = await crud_user.get_user_by_email(db, email=email)

        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None

        return user

    def create_jwt_token(self, user: User) -> str:
        """Generates JWT token for the user."""

        access_token = create_access_token(
            data={"sub": user.email}
        )
        return access_token
