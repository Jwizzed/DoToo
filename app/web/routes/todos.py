import logging
from datetime import date
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
    Query,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import get_db
from app.db.models import User, Todo
from app.schemas.todo import TodoCreate, TodoUpdate, PRIORITY_MAP, VALID_PRIORITIES
from app.services.orchestrator_service import get_orchestrator, OrchestratorService
from app.web.deps import get_current_active_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

TODO_STATUS_OPTIONS = ["Not Started", "In Progress", "Done"]
TODO_PRIORITY_OPTIONS = PRIORITY_MAP
TODO_SORT_OPTIONS = {
    "created_at": "Created Date (Newest First)",
    "created_at_asc": "Created Date (Oldest First)",
    "due_date_asc": "Due Date (Soonest First)",
    "due_date_desc": "Due Date (Latest First)",
    "priority_asc": "Priority (High First)",
    "priority_desc": "Priority (Low First)",
}


def try_parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


@router.get("/", response_class=HTMLResponse, name="web_read_todos")
async def read_todos_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    current_user: User = Depends(get_current_active_user_from_cookie),
    filter_status: Optional[str] = Query(None, alias="status"),
    filter_priority: Optional[str] = Query(None, alias="priority"),
    sort_by: Optional[str] = Query("created_at", alias="sort"),
    search_term: Optional[str] = Query(None, alias="search"),
):
    """Displays the main todo list page for the logged-in user with filtering/sorting."""
    print(
        f"Route Handler: Fetching todos for user {current_user.email} via orchestrator..."
    )

    if filter_status and filter_status not in TODO_STATUS_OPTIONS:
        filter_status = None
    if sort_by not in TODO_SORT_OPTIONS:
        sort_by = "created_at"

    priority_int = try_parse_int(filter_priority)
    if priority_int is not None and priority_int not in VALID_PRIORITIES:
        priority_int = None

    try:
        todos_from_db: List[Todo] = await orchestrator.get_todos_for_user(
            db=db,
            user=current_user,
            filter_status=filter_status,
            filter_priority=priority_int,
            sort_by=sort_by,
            search_term=search_term,
        )
    except Exception as e:
        logging.exception("Error fetching todos in route handler")
        today = date.today()

        return templates.TemplateResponse(
            "todos.html",
            {
                "request": request,
                "todos": [],
                "current_user": current_user,
                "status_options": TODO_STATUS_OPTIONS,
                "priority_options": TODO_PRIORITY_OPTIONS,
                "sort_options": TODO_SORT_OPTIONS,
                "filters": {
                    "status": filter_status,
                    "priority": filter_priority,
                    "sort": sort_by,
                    "search": search_term,
                },
                "error": f"An error occurred while fetching todos: {e}",
                "message": None,
                "today_date": today,
                "priority_map": PRIORITY_MAP,
            },
            status_code=500,
        )

    todos_for_template: List[dict[str, Any]] = []
    if settings.CLOUDINARY_URL:
        for todo in todos_from_db:
            todo_dict = todo.__dict__.copy()
            todo_dict["priority_str"] = PRIORITY_MAP.get(todo.priority, "Unknown")
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
        todos_for_template = []
        for todo in todos_from_db:
            todo_dict = todo.__dict__.copy()
            todo_dict["priority_str"] = PRIORITY_MAP.get(todo.priority, "Unknown")
            todos_for_template.append(todo_dict)

    today = date.today()
    print("Route Handler: Data fetched. Rendering todo list template...")
    return templates.TemplateResponse(
        "todos.html",
        {
            "request": request,
            "todos": todos_for_template,
            "current_user": current_user,
            "status_options": TODO_STATUS_OPTIONS,
            "priority_options": TODO_PRIORITY_OPTIONS,
            "sort_options": TODO_SORT_OPTIONS,
            "priority_map": PRIORITY_MAP,
            "filters": {
                "status": filter_status,
                "priority": filter_priority,
                "sort": sort_by,
                "search": search_term,
            },
            "error": request.query_params.get("error"),
            "message": request.query_params.get("message"),
            "today_date": today,
        },
    )


@router.post("/add", name="web_add_todo")
async def add_todo_action(
    request: Request,
    db: AsyncSession = Depends(get_db),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    due_date_str: Optional[str] = Form(None, alias="due_date"),
    priority: int = Form(..., ge=min(VALID_PRIORITIES), le=max(VALID_PRIORITIES)),
    photo: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user_from_cookie),
):
    """Handles the form submission for adding a new todo item."""
    uploaded_photo = photo if photo and photo.filename else None
    print(f"Route Handler: Preparing data for new todo '{title}'...")

    due_date_obj: Optional[date] = None
    if due_date_str:
        try:
            due_date_obj = date.fromisoformat(due_date_str)
        except ValueError:

            redirect_url = request.url_for("web_read_todos").include_query_params(
                error="Invalid due date format. Please use YYYY-MM-DD."
            )
            return RedirectResponse(
                url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
            )

    try:
        todo_in = TodoCreate(
            title=title,
            description=description,
            due_date=due_date_obj,
            priority=priority,
        )
    except ValidationError as e:

        error_message = f"Invalid input: {e}"
        redirect_url = request.url_for("web_read_todos").include_query_params(
            error=error_message
        )
        return RedirectResponse(
            url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
        )

    error_message = None
    try:
        print(
            f"Route Handler: Calling orchestrator to add todo for user {current_user.email}..."
        )
        await orchestrator.add_todo_for_user(
            db=db, todo_in=todo_in, user=current_user, photo=uploaded_photo
        )
        print("Route Handler: Add todo successful. Redirecting...")
        redirect_url = request.url_for("web_read_todos").include_query_params(
            message="Todo added successfully."
        )
        return RedirectResponse(
            url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
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


@router.get("/edit/{todo_id}", response_class=HTMLResponse, name="web_edit_todo_form")
async def edit_todo_form(
    request: Request,
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    current_user: User = Depends(get_current_active_user_from_cookie),
):
    """Displays the form to edit an existing todo item."""
    print(f"Route Handler: Getting todo ID {todo_id} for edit form...")
    todo = None
    photo_url = None

    try:
        todo = await orchestrator.get_single_todo_for_user(
            db=db, todo_id=todo_id, user=current_user
        )

        if todo and todo.photo_filename and settings.CLOUDINARY_URL:
            try:
                url_options = cloudinary.utils.cloudinary_url(
                    todo.photo_filename,
                    secure=True,
                    fetch_format="auto",
                    quality="auto",
                    width=150,
                    height=150,
                    crop="limit",
                )
                photo_url = url_options[0]
                print(f"Generated Cloudinary URL: {photo_url}")
            except Exception as e:
                logging.error(
                    f"Error generating Cloudinary URL in edit form for {todo.photo_filename}: {e}"
                )

    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            error_message = "Todo not found or you don't have permission to edit it."
            redirect_url = request.url_for("web_read_todos").include_query_params(
                error=error_message
            )
            return RedirectResponse(
                url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
            )
        else:
            raise e
    except Exception as e:
        logging.exception(f"Unexpected error fetching todo {todo_id} for edit")
        error_message = "An unexpected error occurred while trying to edit the todo."
        redirect_url = request.url_for("web_read_todos").include_query_params(
            error=error_message
        )
        return RedirectResponse(
            url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
        )

    if not todo:
        error_message = "Could not load todo item for editing."
        redirect_url = request.url_for("web_read_todos").include_query_params(
            error=error_message
        )
        return RedirectResponse(
            url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
        )

    print("Route Handler: Rendering edit form...")
    return templates.TemplateResponse(
        "edit_todo.html",
        {
            "request": request,
            "todo": todo,
            "current_user": current_user,
            "priority_options": TODO_PRIORITY_OPTIONS,
            "photo_url": photo_url,
            "error": request.query_params.get("error"),
        },
    )


@router.post("/edit/{todo_id}", name="web_edit_todo_action")
async def edit_todo_action(
    request: Request,
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    due_date_str: Optional[str] = Form(None, alias="due_date"),
    priority: int = Form(..., ge=min(VALID_PRIORITIES), le=max(VALID_PRIORITIES)),
    current_user: User = Depends(get_current_active_user_from_cookie),
):
    """Handles the form submission for editing a todo item."""
    print(f"Route Handler: Processing edit for todo ID {todo_id}...")

    due_date_obj: Optional[date] = None
    if due_date_str:
        try:
            due_date_obj = date.fromisoformat(due_date_str)
        except ValueError:

            edit_form_url = request.url_for("web_edit_todo_form", todo_id=todo_id)
            redirect_url = edit_form_url.include_query_params(
                error="Invalid due date format. Please use YYYY-MM-DD."
            )
            return RedirectResponse(
                url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
            )

    try:
        todo_update_data = TodoUpdate(
            title=title,
            description=description,
            due_date=due_date_obj,
            priority=priority,
        )
    except ValidationError as e:

        edit_form_url = request.url_for("web_edit_todo_form", todo_id=todo_id)
        redirect_url = edit_form_url.include_query_params(error=f"Invalid input: {e}")
        return RedirectResponse(
            url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
        )

    error_message = None
    success_message = None
    try:
        print(f"Route Handler: Calling orchestrator to update todo ID {todo_id}...")
        await orchestrator.update_todo_for_user(
            db=db, todo_id=todo_id, todo_in=todo_update_data, user=current_user
        )
        print("Route Handler: Edit successful. Redirecting to list...")
        success_message = "Todo updated successfully."

    except HTTPException as e:
        print(
            f"Route Handler: Edit failed (HTTPException {e.status_code}) - {e.detail}."
        )
        if e.status_code == status.HTTP_404_NOT_FOUND:
            error_message = "Todo not found or you don't have permission to edit it."
        else:
            error_message = e.detail
    except Exception as e:
        print(f"Route Handler: Edit failed (Unexpected Exception) - {e}.")
        logging.exception(f"Unexpected error during edit_todo_action for {todo_id}")
        error_message = "An unexpected error occurred while updating the todo."

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


@router.post("/update/{todo_id}/status", name="web_update_todo_status")
async def update_todo_status_action(
    request: Request,
    todo_id: int,
    status_val: str = Form(..., alias="status"),
    db: AsyncSession = Depends(get_db),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    current_user: User = Depends(get_current_active_user_from_cookie),
):
    """Handles the form submission for updating ONLY a todo item's status."""
    print(
        f"Route Handler: Validating status update '{status_val}' for todo ID {todo_id}..."
    )

    if status_val not in TODO_STATUS_OPTIONS:
        print("Route Handler: Invalid status value. Redirecting with error...")
        redirect_url = request.url_for("web_read_todos").include_query_params(
            error="Invalid status value provided."
        )
        return RedirectResponse(
            url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
        )

    print("Route Handler: Preparing update data (status only)...")
    todo_update = TodoUpdate(status=status_val)

    error_message = None
    try:
        print(
            f"Route Handler: Calling orchestrator to update todo ID {todo_id} status..."
        )
        await orchestrator.update_todo_for_user(
            db=db, todo_id=todo_id, todo_in=todo_update, user=current_user
        )
        print("Route Handler: Status update successful. Redirecting...")
        redirect_url = request.url_for("web_read_todos").include_query_params(
            message="Todo status updated."
        )
        return RedirectResponse(
            url=str(redirect_url), status_code=status.HTTP_303_SEE_OTHER
        )

    except HTTPException as e:
        print(
            f"Route Handler: Status update failed (HTTPException {e.status_code}) - {e.detail}."
        )
        if e.status_code == status.HTTP_404_NOT_FOUND:
            error_message = "Todo not found or you don't have permission to update it."
        else:
            error_message = e.detail
    except Exception as e:
        print(f"Route Handler: Status update failed (Unexpected Exception) - {e}.")
        logging.exception("Unexpected error during update_todo_status_action")
        error_message = "An unexpected error occurred while updating the todo status."

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
            f"Route Handler: Delete failed (HTTPException {e.status_code}) - {e.detail}."
        )
        if e.status_code == status.HTTP_404_NOT_FOUND:
            error_message = "Todo not found or you don't have permission to delete it."
        else:
            error_message = e.detail
    except Exception as e:
        print(f"Route Handler: Delete failed (Unexpected Exception) - {e}.")
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
