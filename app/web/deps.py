from typing import Optional

from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.crud import crud_user
from app.db.base import get_db
from app.db.models import User


async def get_current_user_from_cookie(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get the current user from the access token stored in a cookie.
    Returns the user object or None if not authenticated or invalid token.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None

    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    email = decode_access_token(token)
    if email is None:
        return None

    user = await crud_user.get_user_by_email(db, email=email)
    if user is None or not user.is_active:
        return None

    return user


async def get_current_active_user_from_cookie(
    current_user: Optional[User] = Depends(get_current_user_from_cookie),
) -> User:
    """
    Dependency to get the current active user. Raises 401 if not authenticated.
    Use this to protect routes.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
