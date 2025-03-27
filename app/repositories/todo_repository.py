from typing import List, Optional

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.todo import TodoCreate, TodoUpdate
from app.db.models import Todo


class TodoRepository:
    """
    Handles database operations for Todo model.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_todo_by_id(self, todo_id: int, owner_id: int) -> Optional[Todo]:
        """Fetches a specific todo by ID, ensuring ownership."""
        result = await self.db.execute(
            select(Todo)
            .filter(Todo.id == todo_id, Todo.owner_id == owner_id)
        )
        return result.scalars().first()

    async def get_all_todos_by_owner(self, owner_id: int, skip: int = 0, limit: int = 100) -> List[Todo]:
        """Fetches all todos for a specific owner with pagination."""
        result = await self.db.execute(
            select(Todo)
            .filter(Todo.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .order_by(Todo.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_todo(self, todo_in: TodoCreate, owner_id: int, image_url: Optional[str] = None) -> Todo:
        """Creates a new todo item."""
        db_todo = Todo(
            title=todo_in.title,
            description=todo_in.description,
            owner_id=owner_id,
            image_url=image_url
        )
        self.db.add(db_todo)
        await self.db.commit()
        await self.db.refresh(db_todo)
        return db_todo

    async def update_todo(self, todo_id: int, owner_id: int, todo_update: TodoUpdate) -> Optional[Todo]:
        """Updates an existing todo item."""
        db_todo = await self.get_todo_by_id(todo_id, owner_id)
        if not db_todo:
            return None

        # Get update data, excluding unset fields
        update_data = todo_update.model_dump(exclude_unset=True)

        if not update_data:
            return db_todo

        # Perform the update
        await self.db.execute(
            update(Todo)
            .where(Todo.id == todo_id, Todo.owner_id == owner_id)
            .values(**update_data)
        )
        await self.db.commit()
        await self.db.refresh(db_todo)
        return db_todo

    async def delete_todo(self, todo_id: int, owner_id: int) -> Optional[Todo]:
        """Deletes a todo item."""
        db_todo = await self.get_todo_by_id(todo_id, owner_id)
        if not db_todo:
            return None

        await self.db.execute(
            delete(Todo).where(Todo.id == todo_id, Todo.owner_id == owner_id)
        )
        await self.db.commit()
        return db_todo
