from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.user import UserCreate
from app.services.auth_service import auth_service

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/login", response_class=HTMLResponse, name="web_login_form")
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", name="web_login")
async def login_for_access_token(
        response: Response,
        request: Request,
        db: AsyncSession = Depends(get_db),
        email: str = Form(...),
        password: str = Form(...)
):
    user = await auth_service.authenticate_user(db, email=email, password=password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Incorrect email or password"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    access_token = auth_service.create_jwt_token(user)

    response = RedirectResponse(url=router.url_path_for("web_read_todos"), status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
    )
    return response



@router.get("/logout", name="web_logout")
async def logout(response: Response):
    response = RedirectResponse(url=router.url_path_for("web_login_form"), status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response


@router.get("/signup", response_class=HTMLResponse, name="web_signup_form")
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup", name="web_signup")
async def create_user(
        request: Request,
        db: AsyncSession = Depends(get_db),
        email: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...)
):
    if password != confirm_password:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Passwords do not match"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    user_in = UserCreate(email=email, password=password)
    try:
        await auth_service.register_user(db=db, user_in=user_in)
        return RedirectResponse(url=router.url_path_for("web_login_form") + "?message=Signup+successful.+Please+login.",
                                status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": e.detail},
            status_code=e.status_code
        )
