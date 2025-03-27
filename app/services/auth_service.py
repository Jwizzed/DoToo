from datetime import timedelta

from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.schemas.auth import Token
from app.api.v1.schemas.user import UserCreate
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.db.models import User
from app.exceptions.base import CredentialsException, DuplicateEntryException
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, user_in: UserCreate) -> User:
        """Registers a new user."""
        existing_user = await self.user_repo.get_user_by_username(user_in.username)
        if existing_user:
            raise DuplicateEntryException(detail=f"Username '{user_in.username}' already registered.")
        existing_email = await self.user_repo.get_user_by_email(user_in.email)
        if existing_email:
            raise DuplicateEntryException(detail=f"Email '{user_in.email}' already registered.")

        hashed_password = get_password_hash(user_in.password)
        new_user = await self.user_repo.create_user(user_in, hashed_password)
        return new_user

    async def authenticate_user(self, form_data: OAuth2PasswordRequestForm) -> Token:
        """Authenticates a user and returns a JWT token."""
        user = await self.user_repo.get_user_by_username(form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise CredentialsException(detail="Incorrect username or password")
        if not user.is_active:
            raise CredentialsException(detail="Inactive user")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")
