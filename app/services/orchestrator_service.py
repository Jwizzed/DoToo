from typing import List, Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Todo
from app.schemas.todo import TodoCreate, TodoUpdate
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.services.todo_service import TodoService


class OrchestratorService:
    """
    Orchestrates actions involving multiple services or complex workflows.
    Acts as the primary entry point for business logic from the presentation layer.
    """

    def __init__(self):
        self.auth_service = AuthService()
        self.todo_service = TodoService()

    async def handle_signup(self, db: AsyncSession, user_in: UserCreate) -> User:
        """Orchestrates the user signup process."""
        print("Orchestrator: Handling signup...")
        user = await self.auth_service.register_user(db=db, user_in=user_in)
        print("Orchestrator: Signup handled.")
        return user

    async def handle_login(
        self, db: AsyncSession, email: str, password: str
    ) -> tuple[Optional[User], Optional[str]]:
        """Orchestrates the user login process."""

        print("Orchestrator: Handling login...")
        user = await self.auth_service.authenticate_user(
            db=db, email=email, password=password
        )
        if not user:
            print("Orchestrator: Login failed - authentication.")
            return None, None

        token = self.auth_service.create_jwt_token(user)
        print("Orchestrator: Login successful, token generated.")
        return user, token

    async def get_todos_for_user(self, db: AsyncSession, user: User) -> List[Todo]:
        """Orchestrates fetching todos for a specific user."""
        print(f"Orchestrator: Getting todos for user {user.email}")

        todos = await self.todo_service.get_user_todos(db=db, user=user)
        print(f"Orchestrator: Found {len(todos)} todos.")
        return todos

    async def add_todo_for_user(
        self,
        db: AsyncSession,
        todo_in: TodoCreate,
        user: User,
        photo: Optional[UploadFile] = None,
    ) -> Todo:
        """Orchestrates adding a new todo for a user."""
        print(f"Orchestrator: Adding todo '{todo_in.title}' for user {user.email}")

        try:
            todo = await self.todo_service.create_new_todo(
                db=db, todo_in=todo_in, user=user, photo=photo
            )
            print(f"Orchestrator: Todo added successfully (ID: {todo.id}).")
            return todo
        except HTTPException as e:
            print(f"Orchestrator: Error adding todo - {e.detail}")
            raise e
        except Exception as e:
            print(f"Orchestrator: Unexpected error adding todo - {e}")

            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while adding the todo.",
            )

    async def update_todo_for_user(
        self, db: AsyncSession, todo_id: int, todo_in: TodoUpdate, user: User
    ) -> Todo:
        """Orchestrates updating a todo for a user."""
        print(f"Orchestrator: Updating todo ID {todo_id} for user {user.email}")

        try:
            updated_todo = await self.todo_service.update_existing_todo(
                db=db, todo_id=todo_id, todo_in=todo_in, user=user
            )
            print(f"Orchestrator: Todo ID {todo_id} updated successfully.")
            return updated_todo
        except HTTPException as e:
            print(f"Orchestrator: Error updating todo - {e.detail}")
            raise e
        except Exception as e:
            print(f"Orchestrator: Unexpected error updating todo - {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while updating the todo.",
            )

    async def delete_todo_for_user(
        self, db: AsyncSession, todo_id: int, user: User
    ) -> None:
        """Orchestrates deleting a todo for a user."""
        print(f"Orchestrator: Deleting todo ID {todo_id} for user {user.email}")

        try:
            await self.todo_service.delete_existing_todo(
                db=db, todo_id=todo_id, user=user
            )
            print(f"Orchestrator: Todo ID {todo_id} deleted successfully.")
        except HTTPException as e:
            print(f"Orchestrator: Error deleting todo - {e.detail}")
            raise e
        except Exception as e:
            print(f"Orchestrator: Unexpected error deleting todo - {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while deleting the todo.",
            )


def get_orchestrator() -> OrchestratorService:
    return OrchestratorService()
