from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.base import create_tables
from app.web.routes import auth as web_auth_router
from app.web.routes import todos as web_todos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup...")
    print("Creating database tables...")
    await create_tables()
    print("Database tables checked/created.")
    yield
    print("Application shutdown...")


app = FastAPI(
    title="Todo Application",
    description="Full-stack Todo App with FastAPI and Jinja2",
    version="0.1.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

app.include_router(web_auth_router.router, tags=["Web Authentication"], prefix="/auth")
app.include_router(web_todos_router.router, tags=["Web Todos"],
                   prefix="/todos")


@app.get("/", tags=["Root"], include_in_schema=False)
async def read_root(request: Request):
    if request.cookies.get("access_token"):
        return RedirectResponse(url=request.url_for("web_read_todos"))
    else:
        return RedirectResponse(url=request.url_for("web_login_form"))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    is_web_request = request.url.path.startswith("/todos") or request.url.path.startswith("/auth")

    if exc.status_code == status.HTTP_401_UNAUTHORIZED and is_web_request:
        login_url = request.url_for('web_login_form')
        response = RedirectResponse(url=str(login_url), status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie("access_token")
        return response

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )
