import logging
from typing import Optional, List, Any

import cloudinary
import cloudinary.utils
from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    HTTPException,
    status,
    UploadFile,
    File,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import get_db
from app.db.models import User, Todo
from app.schemas.todo import TodoCreate, TodoUpdate
from app.services.orchestrator_service import get_orchestrator, OrchestratorService
from app.web.deps import get_current_active_user_from_cookie


router = APIRouter()

templates = Jinja2Templates(directory="app/web/templates")

TODO_STATUS_OPTIONS = ["Not Started", "In Progress", "Done"]


@router.get("/", response_class=HTMLResponse, name="web_read_todos")
async def read_todos_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    current_user: User = Depends(get_current_active_user_from_cookie),
):
    """Displays the main todo list page for the logged-in user."""

    print(
        f"Route Handler: Fetching todos for user {current_user.email} via orchestrator..."
    )

    todos_from_db: List[Todo] = await orchestrator.get_todos_for_user(
        db=db, user=current_user
    )

    todos_for_template: List[dict[str, Any]] = []

    if settings.CLOUDINARY_URL:

        for todo in todos_from_db:

            todo_dict = todo.__dict__

            if todo.photo_filename:

                try:

                    url, options = cloudinary.utils.cloudinary_url(
                        todo.photo_filename,
                        secure=True,
                        fetch_format="auto",
                        quality="auto",
                    )

                    todo_dict["photo_url"] = url

                except Exception as e:

                    logging.error(
                        f"Error generating Cloudinary URL for {todo.photo_filename}: {e}"
                    )

                    todo_dict["photo_url"] = None

            else:

                todo_dict["photo_url"] = None

            todos_for_template.append(todo_dict)

    else:

        logging.warning("Cloudinary not configured, photo URLs will not be generated.")

        todos_for_template = [todo.__dict__ for todo in todos_from_db]

    print("Route Handler: Data fetched. Rendering todo list template...")

    return templates.TemplateResponse(
        "todos.html",
        {
            "request": request,
            "todos": todos_for_template,
            "current_user": current_user,
            "status_options": TODO_STATUS_OPTIONS,
            "error": request.query_params.get("error"),
            "message": request.query_params.get("message"),
        },
    )


@router.post("/add", name="web_add_todo")
async def add_todo_action(
    request: Request,
    db: AsyncSession = Depends(get_db),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user_from_cookie),
):
    """Handles the form submission for adding a new todo item."""

    uploaded_photo = photo if photo and photo.filename else None

    print(f"Route Handler: Preparing data for new todo '{title}'...")

    todo_in = TodoCreate(title=title, description=description)

    error_message = None

    try:

        print(
            f"Route Handler: Calling orchestrator to add todo for user {current_user.email}..."
        )

        await orchestrator.add_todo_for_user(
            db=db, todo_in=todo_in, user=current_user, photo=uploaded_photo
        )

        print("Route Handler: Add todo successful. Redirecting...")

        return RedirectResponse(
            url=request.url_for("web_read_todos"), status_code=status.HTTP_303_SEE_OTHER
        )

    except HTTPException as e:

        print(
            f"Route Handler: Add todo failed (HTTPException {e.status_code}) - {e.detail}. Redirecting with error..."
        )

        error_message = e.detail

    except Exception as e:

        print(
            f"Route Handler: Add todo failed (Unexpected Exception) - {e}. Redirecting with error..."
        )

        logging.exception("Unexpected error during add_todo_action")

        error_message = "An unexpected error occurred while adding the todo."

    redirect_url = request.url_for("web_read_todos").include_query_params(
        error=error_message
    )

    return RedirectResponse(
        url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/update/{todo_id}/status", name="web_update_todo_status")
async def update_todo_status_action(
    request: Request,
    todo_id: int,
    status_val: str = Form(..., alias="status"),
    db: AsyncSession = Depends(get_db),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    current_user: User = Depends(get_current_active_user_from_cookie),
):
    """Handles the form submission for updating a todo item's status."""

    print(
        f"Route Handler: Validating status update '{status_val}' for todo ID {todo_id}..."
    )

    if status_val not in TODO_STATUS_OPTIONS:
        print("Route Handler: Invalid status value. Redirecting with error...")

        redirect_url = request.url_for("web_read_todos").include_query_params(
            error="Invalid status value."
        )

        return RedirectResponse(
            url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
        )

    print("Route Handler: Preparing update data...")

    todo_update = TodoUpdate(status=status_val)

    error_message = None

    try:

        print(f"Route Handler: Calling orchestrator to update todo ID {todo_id}...")

        await orchestrator.update_todo_for_user(
            db=db, todo_id=todo_id, todo_in=todo_update, user=current_user
        )

        print("Route Handler: Update successful. Redirecting...")

        return RedirectResponse(
            url=request.url_for("web_read_todos"), status_code=status.HTTP_303_SEE_OTHER
        )

    except HTTPException as e:

        print(
            f"Route Handler: Update failed (HTTPException {e.status_code}) - {e.detail}. Redirecting with error..."
        )

        error_message = e.detail

    except Exception as e:

        print(
            f"Route Handler: Update failed (Unexpected Exception) - {e}. Redirecting with error..."
        )

        logging.exception("Unexpected error during update_todo_status_action")

        error_message = "An unexpected error occurred while updating the todo."

    redirect_url = request.url_for("web_read_todos").include_query_params(
        error=error_message
    )

    return RedirectResponse(
        url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/delete/{todo_id}", name="web_delete_todo")
async def delete_todo_action(
    request: Request,
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    current_user: User = Depends(get_current_active_user_from_cookie),
):
    """Handles the form submission for deleting a todo item."""

    error_message = None

    success_message = None

    try:

        print(f"Route Handler: Calling orchestrator to delete todo ID {todo_id}...")

        await orchestrator.delete_todo_for_user(
            db=db, todo_id=todo_id, user=current_user
        )

        print("Route Handler: Delete successful. Redirecting...")

        success_message = "Todo deleted successfully."

    except HTTPException as e:

        print(
            f"Route Handler: Delete failed (HTTPException {e.status_code}) - {e.detail}. Redirecting with error..."
        )

        error_message = e.detail

    except Exception as e:

        print(
            f"Route Handler: Delete failed (Unexpected Exception) - {e}. Redirecting with error..."
        )

        logging.exception("Unexpected error during delete_todo_action")

        error_message = "An unexpected error occurred while deleting the todo."

    query_params = {}

    if error_message:
        query_params["error"] = error_message

    if success_message:
        query_params["message"] = success_message

    redirect_url = request.url_for("web_read_todos").include_query_params(
        **query_params
    )

    return RedirectResponse(
        url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
    )
