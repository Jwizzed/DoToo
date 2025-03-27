from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v1 import schemas
from app.db.base import get_db
from app.db.models import User
from app.exceptions.base import NotFoundException, FileUploadException
from app.repositories.todo_repository import TodoRepository
from app.services.todo_service import TodoService

router = APIRouter()


def get_todo_service(db: AsyncSession = Depends(get_db)) -> TodoService:
    repo = TodoRepository(db)
    return TodoService(repo)


@router.get("/", response_model=List[schemas.todo.TodoRead])
async def read_todos(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(deps.get_current_active_user),
        todo_service: TodoService = Depends(get_todo_service),
):
    """
    Retrieve todo items for the current user.
    """
    todos = await todo_service.get_todos(current_user=current_user, skip=skip, limit=limit)
    return todos


@router.post("/", response_model=schemas.todo.TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(
        *,
        # Use Form(...) for form fields when mixing with File(...)
        title: str = Form(...),
        description: Optional[str] = Form(None),
        image_file: Optional[UploadFile] = File(None, description="Optional image file for the todo item"),
        background_tasks: BackgroundTasks,
        current_user: User = Depends(deps.get_current_active_user),
        todo_service: TodoService = Depends(get_todo_service),
):
    """
    Create new todo item. Optionally upload an image.
    """
    todo_in = schemas.todo.TodoCreate(title=title, description=description)
    try:
        new_todo = await todo_service.create_new_todo(
            todo_in=todo_in,
            current_user=current_user,
            background_tasks=background_tasks,
            image_file=image_file
        )
        return new_todo
    except FileUploadException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
    except Exception as e:
        # Log the exception e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the todo.",
        )


@router.get("/{todo_id}", response_model=schemas.todo.TodoRead)
async def read_todo(
        todo_id: int,
        current_user: User = Depends(deps.get_current_active_user),
        todo_service: TodoService = Depends(get_todo_service),
):
    """
    Get a specific todo by ID.
    """
    try:
        todo = await todo_service.get_todo(todo_id=todo_id, current_user=current_user)
        return todo
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)


@router.put("/{todo_id}", response_model=schemas.todo.TodoRead)
async def update_todo(
        todo_id: int,
        todo_in: schemas.todo.TodoUpdate,  # Request body
        current_user: User = Depends(deps.get_current_active_user),
        todo_service: TodoService = Depends(get_todo_service),
):
    """
    Update a todo item.
    """
    try:
        updated_todo = await todo_service.update_existing_todo(
            todo_id=todo_id,
            todo_update=todo_in,
            current_user=current_user
        )
        return updated_todo
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        # Log exception e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the todo.",
        )


@router.delete("/{todo_id}", response_model=schemas.todo.TodoRead)  # Or return status_code=204
async def delete_todo(
        todo_id: int,
        current_user: User = Depends(deps.get_current_active_user),
        todo_service: TodoService = Depends(get_todo_service),
):
    """
    Delete a todo item.
    """
    try:
        deleted_todo = await todo_service.delete_existing_todo(
            todo_id=todo_id,
            current_user=current_user
        )
        # Return the deleted item or just a confirmation
        return deleted_todo
        # Alternatively, for 204 No Content:
        # return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        # Log exception e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the todo.",
        )
