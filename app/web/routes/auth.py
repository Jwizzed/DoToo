from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.user import UserCreate
from app.services.orchestrator_service import get_orchestrator, OrchestratorService

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/login", response_class=HTMLResponse, name="web_login_form")
async def login_form(request: Request):
    """Displays the login form page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", name="web_login")
async def login_for_access_token(
        response: Response,
        request: Request,
        db: AsyncSession = Depends(get_db),
        orchestrator: OrchestratorService = Depends(get_orchestrator),
        email: str = Form(...),
        password: str = Form(...)
):
    """Handles the login form submission."""

    print("Route Handler: Attempting login via orchestrator...")
    user, access_token = await orchestrator.handle_login(db=db, email=email, password=password)

    if not user or not access_token:
        print("Route Handler: Login failed. Rendering login form with error.")

        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Incorrect email or password"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    print("Route Handler: Login successful. Setting cookie and redirecting...")

    response = RedirectResponse(url=request.url_for("web_read_todos"), status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,
        samesite="lax"
    )
    return response


@router.get("/logout", name="web_logout")
async def logout(request: Request):
    """Handles user logout by clearing the cookie and redirecting."""

    print("Route Handler: Logging out...")

    response = RedirectResponse(url=request.url_for("web_login_form"), status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    print("Route Handler: Cookie cleared. Redirecting to login.")
    return response


@router.get("/signup", response_class=HTMLResponse, name="web_signup_form")
async def signup_form(request: Request):
    """Displays the signup form page."""
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup", name="web_signup")
async def create_user(
        request: Request,
        db: AsyncSession = Depends(get_db),
        orchestrator: OrchestratorService = Depends(get_orchestrator),
        email: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...)
):
    """Handles the signup form submission."""

    if password != confirm_password:
        print("Route Handler: Signup failed - Passwords do not match.")
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Passwords do not match"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    user_in = UserCreate(email=email, password=password)
    try:

        print("Route Handler: Attempting signup via orchestrator...")
        await orchestrator.handle_signup(db=db, user_in=user_in)

        print("Route Handler: Signup successful. Redirecting to login.")

        return RedirectResponse(url=request.url_for("web_login_form") + "?message=Signup+successful.+Please+login.",
                                status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:

        print(f"Route Handler: Signup failed - {e.detail}. Rendering signup form with error.")

        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": e.detail},
            status_code=e.status_code
        )
    except Exception as e:

        print(f"Route Handler: Unexpected signup error - {e}. Rendering signup form with error.")
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "An unexpected error occurred during signup."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
