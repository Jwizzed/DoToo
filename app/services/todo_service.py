import os
import shutil
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud import crud_todo
from app.db.models import Todo, User
from app.schemas.todo import TodoCreate, TodoUpdate


class TodoService:
    async def get_user_todos(self, db: AsyncSession, user: User) -> List[Todo]:
        """Get all todos for the current user."""

        return await crud_todo.get_todos_by_owner(db=db, owner_id=user.id)

    async def create_new_todo(
            self,
            db: AsyncSession,
            todo_in: TodoCreate,
            user: User,
            photo: Optional[UploadFile] = None
    ) -> Todo:
        """Create a new todo item, optionally handling file upload."""
        photo_filename = None
        if photo and photo.filename:

            if not photo.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file type. Only images are allowed."
                )

            file_extension = Path(photo.filename).suffix
            photo_filename = f"{uuid4()}{file_extension}"
            save_path = settings.UPLOADS_DIR / photo_filename
            try:

                with open(save_path, "wb") as buffer:
                    shutil.copyfileobj(photo.file, buffer)
            except Exception as e:
                if save_path.exists():
                    os.remove(save_path)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not save file: {e}",
                )
            finally:
                await photo.close()

        todo = await crud_todo.create_todo(
            db=db,
            todo_in=todo_in,
            owner_id=user.id,
            photo_filename=photo_filename
        )
        return todo

    async def update_existing_todo(
            self,
            db: AsyncSession,
            todo_id: int,
            todo_in: TodoUpdate,
            user: User
    ) -> Todo:
        """Update an existing todo item."""

        db_todo = await crud_todo.get_todo(db=db, todo_id=todo_id, owner_id=user.id)
        if not db_todo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

        updated_todo = await crud_todo.update_todo(db=db, db_todo=db_todo, todo_in=todo_in)
        return updated_todo

    async def delete_existing_todo(self, db: AsyncSession, todo_id: int, user: User) -> None:
        """Delete an existing todo item."""

        db_todo = await crud_todo.get_todo(db=db, todo_id=todo_id, owner_id=user.id)
        if not db_todo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

        if db_todo.photo_filename:
            photo_path = settings.UPLOADS_DIR / db_todo.photo_filename
            if photo_path.exists():
                try:
                    os.remove(photo_path)
                except OSError as e:
                    print(f"Error deleting file {photo_path}: {e}")

        await crud_todo.delete_todo(db=db, todo_id=todo_id, owner_id=user.id)
