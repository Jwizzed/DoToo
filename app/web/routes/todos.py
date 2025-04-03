from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import User
from app.schemas.todo import TodoCreate, TodoUpdate
from app.services.todo_service import todo_service
from app.web.deps import get_current_active_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

TODO_STATUS_OPTIONS = ["Not Started", "In Progress", "Done"]


@router.get("/", response_class=HTMLResponse, name="web_read_todos")
async def read_todos_page(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user_from_cookie)
):
    todos = await todo_service.get_user_todos(db=db, user=current_user)
    return templates.TemplateResponse(
        "todos.html",
        {
            "request": request,
            "todos": todos,
            "current_user": current_user,
            "status_options": TODO_STATUS_OPTIONS,
            "error": request.query_params.get("error"),
            "message": request.query_params.get("message")
        }
    )


@router.post("/add", name="web_add_todo")
async def add_todo_action(
        request: Request,
        db: AsyncSession = Depends(get_db),
        title: str = Form(...),
        description: Optional[str] = Form(None),
        photo: UploadFile = File(None),
        current_user: User = Depends(get_current_active_user_from_cookie)
):
    todo_in = TodoCreate(title=title, description=description)
    error_message = None
    try:
        await todo_service.create_new_todo(
            db=db, todo_in=todo_in, user=current_user, photo=photo
        )
        return RedirectResponse(url=router.url_path_for("web_read_todos"), status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        error_message = e.detail
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"

    redirect_url = request.url_for('web_read_todos').include_query_params(error=error_message)
    return RedirectResponse(url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER)



@router.post("/update/{todo_id}/status", name="web_update_todo_status")
async def update_todo_status_action(
        request: Request,  # For redirect URL base
        todo_id: int,
        status_val: str = Form(..., alias="status"),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user_from_cookie)
):
    if status_val not in TODO_STATUS_OPTIONS:
        redirect_url = request.url_for('web_read_todos').include_query_params(error="Invalid status value.")
        return RedirectResponse(url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER)

    todo_update = TodoUpdate(status=status_val)
    try:
        await todo_service.update_existing_todo(
            db=db, todo_id=todo_id, todo_in=todo_update, user=current_user
        )
        return RedirectResponse(url=router.url_path_for("web_read_todos"), status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        redirect_url = request.url_for('web_read_todos').include_query_params(error=e.detail)
        return RedirectResponse(url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/delete/{todo_id}", name="web_delete_todo")
async def delete_todo_action(
        request: Request,
        todo_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user_from_cookie)
):
    try:
        await todo_service.delete_existing_todo(db=db, todo_id=todo_id, user=current_user)
        redirect_url = request.url_for('web_read_todos').include_query_params(message="Todo deleted successfully.")
        return RedirectResponse(url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        redirect_url = request.url_for('web_read_todos').include_query_params(error=e.detail)
        return RedirectResponse(url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER)
