from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import auth as auth_schema
from app.api.v1.schemas import user as user_schema
from app.db.base import get_db
from app.events.event_handlers import send_welcome_email
from app.exceptions.base import DuplicateEntryException
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=user_schema.UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
        user_in: user_schema.UserCreate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
):
    """
    Create new user and schedule a background task for welcome email.
    """
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    try:
        new_user = await auth_service.register_user(user_in=user_in)

        background_tasks.add_task(
            send_welcome_email,
            email_to=new_user.email,
            username=new_user.username
        )

        return new_user
    except DuplicateEntryException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail,
        )
    except Exception as e:
        print(f"Error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration.",
        )


@router.post("/login", response_model=auth_schema.Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    try:
        token = await auth_service.authenticate_user(form_data=form_data)
        return token
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login.",
        )
