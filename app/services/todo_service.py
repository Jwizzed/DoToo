import logging
from typing import List, Optional
from uuid import uuid4

import cloudinary
import cloudinary.api
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud import crud_todo
from app.db.models import Todo, User
from app.schemas.todo import TodoCreate, TodoUpdate

if settings.CLOUDINARY_URL:

    try:

        cloudinary.config(cloud_url=settings.CLOUDINARY_URL, secure=True)

        logging.info("Cloudinary configured successfully.")

    except Exception as e:

        logging.error(f"Failed to configure Cloudinary: {e}")


else:

    logging.warning(
        "CLOUDINARY_URL not found in settings. Image uploads will be disabled."
    )


class TodoService:

    async def get_user_todos(self, db: AsyncSession, user: User) -> List[Todo]:
        """Get all todos for the current user."""

        return await crud_todo.get_todos_by_owner(db=db, owner_id=user.id)

    async def create_new_todo(
        self,
        db: AsyncSession,
        todo_in: TodoCreate,
        user: User,
        photo: Optional[UploadFile] = None,
    ) -> Todo:
        """Create a new todo item, optionally uploading photo to Cloudinary."""

        photo_public_id = None

        if photo and photo.filename:

            if not settings.CLOUDINARY_URL:
                logging.warning("Cannot upload photo: Cloudinary is not configured.")

                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Image upload service is not configured.",
                )

            if not photo.content_type or not photo.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file type. Only images are allowed.",
                )

            unique_id = f"todo_{user.id}_{uuid4()}"

            try:

                logging.info(
                    f"Uploading photo to Cloudinary with public_id: {unique_id}"
                )

                upload_result = cloudinary.uploader.upload(
                    photo.file,
                    public_id=unique_id,
                    folder="todo_photos",
                    resource_type="image",
                )

                photo_public_id = upload_result.get("public_id")

                logging.info(
                    f"Cloudinary upload successful. Public ID: {photo_public_id}, URL: {upload_result.get('secure_url')}"
                )

            except CloudinaryError as e:

                logging.error(f"Cloudinary upload failed: {e}")

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not upload file to Cloudinary: {e}",
                )

            except Exception as e:

                logging.error(f"An unexpected error occurred during file upload: {e}")

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An unexpected error occurred during file processing.",
                )

            finally:

                await photo.close()

        todo = await crud_todo.create_todo(
            db=db, todo_in=todo_in, owner_id=user.id, photo_filename=photo_public_id
        )

        return todo

    async def update_existing_todo(
        self, db: AsyncSession, todo_id: int, todo_in: TodoUpdate, user: User
    ) -> Todo:
        """Update an existing todo item."""

        db_todo = await crud_todo.get_todo(db=db, todo_id=todo_id, owner_id=user.id)

        if not db_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
            )

        updated_todo = await crud_todo.update_todo(
            db=db, db_todo=db_todo, todo_in=todo_in
        )

        return updated_todo

    async def delete_existing_todo(
        self, db: AsyncSession, todo_id: int, user: User
    ) -> None:
        """Delete an existing todo item and its associated photo from Cloudinary."""

        db_todo = await crud_todo.get_todo(db=db, todo_id=todo_id, owner_id=user.id)

        if not db_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
            )

        photo_public_id_to_delete = db_todo.photo_filename

        await crud_todo.delete_todo(db=db, todo_id=todo_id, owner_id=user.id)

        if photo_public_id_to_delete:

            if not settings.CLOUDINARY_URL:

                logging.warning(
                    f"Cannot delete photo {photo_public_id_to_delete}: Cloudinary is not configured."
                )

            else:

                try:

                    logging.info(
                        f"Deleting photo from Cloudinary: {photo_public_id_to_delete}"
                    )

                    result = cloudinary.uploader.destroy(
                        photo_public_id_to_delete, resource_type="image"
                    )

                    if result.get("result") == "ok":

                        logging.info(
                            f"Successfully deleted {photo_public_id_to_delete} from Cloudinary."
                        )

                    elif result.get("result") == "not found":

                        logging.warning(
                            f"Photo {photo_public_id_to_delete} not found in Cloudinary (maybe already deleted?)."
                        )

                    else:

                        logging.error(
                            f"Failed to delete {photo_public_id_to_delete} from Cloudinary. Result: {result}"
                        )

                except CloudinaryError as e:

                    logging.error(
                        f"Error deleting photo {photo_public_id_to_delete} from Cloudinary: {e}"
                    )

                except Exception as e:

                    logging.error(
                        f"Unexpected error during Cloudinary deletion of {photo_public_id_to_delete}: {e}"
                    )
