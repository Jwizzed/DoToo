import shutil
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile, BackgroundTasks

from app.api.v1.schemas.todo import TodoCreate, TodoUpdate
from app.core.config import settings
from app.db.models import Todo, User
from app.events.event_handlers import send_todo_creation_notification
from app.exceptions.base import NotFoundException, FileUploadException
from app.repositories.todo_repository import TodoRepository


class TodoService:
    def __init__(self, todo_repo: TodoRepository):
        self.todo_repo = todo_repo

    async def get_todos(self, current_user: User, skip: int = 0, limit: int = 100) -> List[Todo]:
        """Gets all todos for the current user."""
        return await self.todo_repo.get_all_todos_by_owner(owner_id=current_user.id, skip=skip, limit=limit)

    async def get_todo(self, todo_id: int, current_user: User) -> Todo:
        """Gets a specific todo by ID for the current user."""
        todo = await self.todo_repo.get_todo_by_id(todo_id=todo_id, owner_id=current_user.id)
        if not todo:
            raise NotFoundException(detail=f"Todo with id {todo_id} not found or access denied.")
        return todo

    async def create_new_todo(
            self,
            todo_in: TodoCreate,
            current_user: User,
            background_tasks: BackgroundTasks,  # For event handling
            image_file: Optional[UploadFile] = None
    ) -> Todo:
        """Creates a new todo, optionally handles file upload, and triggers background task."""
        image_url = None
        if image_file:
            # Basic validation
            if not image_file.content_type.startswith("image/"):
                raise FileUploadException("Uploaded file is not a valid image.")

            # Generate unique filename and path
            file_extension = Path(image_file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = settings.IMAGES_DIR / unique_filename

            # Save the file (use async file I/O for large files in production)
            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(image_file.file, buffer)
            except Exception as e:
                # Basic error handling, consider more specific exceptions
                raise FileUploadException(f"Could not save image file: {e}")
            finally:
                await image_file.close()  # Ensure file is closed

            image_url = f"{settings.IMAGE_BASE_URL}{unique_filename}"

        new_todo = await self.todo_repo.create_todo(
            todo_in=todo_in,
            owner_id=current_user.id,
            image_url=image_url
        )

        # Trigger background task (Event-Driven aspect)
        background_tasks.add_task(
            send_todo_creation_notification,
            email_to=current_user.email,
            todo_title=new_todo.title
        )

        return new_todo

    async def update_existing_todo(
            self,
            todo_id: int,
            todo_update: TodoUpdate,
            current_user: User
    ) -> Todo:
        """Updates an existing todo for the current user."""
        updated_todo = await self.todo_repo.update_todo(
            todo_id=todo_id,
            owner_id=current_user.id,
            todo_update=todo_update
        )
        if not updated_todo:
            raise NotFoundException(detail=f"Todo with id {todo_id} not found or access denied.")
        return updated_todo

    async def delete_existing_todo(self, todo_id: int, current_user: User) -> Todo:
        """Deletes a todo for the current user."""
        deleted_todo = await self.todo_repo.delete_todo(todo_id=todo_id, owner_id=current_user.id)
        if not deleted_todo:
            raise NotFoundException(detail=f"Todo with id {todo_id} not found or access denied.")
        return deleted_todo
