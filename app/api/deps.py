from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import TokenData
from app.core import security
from app.core.config import settings
from app.db.base import get_db
from app.db.models import User
from app.exceptions.base import CredentialsException, InactiveUserException
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from the token.
    """
    try:
        payload = security.decode_access_token(token)
        token_data = TokenData(**payload)
        if token_data.username is None:
            raise CredentialsException
    except JWTError:
        raise CredentialsException

    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_username(username=token_data.username)

    if user is None:
        raise CredentialsException
    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current *active* authenticated user.
    """
    if not current_user.is_active:
        raise InactiveUserException
    return current_user
