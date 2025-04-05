from typing import List, Optional

from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Todo
from app.schemas.todo import TodoCreate, TodoUpdate


async def get_todos_by_owner(
    db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100
) -> List[Todo]:
    result = await db.execute(
        select(Todo)
        .filter(Todo.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .order_by(Todo.created_at.desc())
    )
    return result.scalars().all()


async def get_todo(db: AsyncSession, todo_id: int, owner_id: int) -> Optional[Todo]:
    result = await db.execute(
        select(Todo).filter(Todo.id == todo_id, Todo.owner_id == owner_id)
    )
    return result.scalars().first()


async def create_todo(
    db: AsyncSession,
    *,
    todo_in: TodoCreate,
    owner_id: int,
    photo_filename: Optional[str] = None
) -> Todo:
    db_todo = Todo(
        **todo_in.model_dump(), owner_id=owner_id, photo_filename=photo_filename
    )
    db.add(db_todo)
    await db.flush()
    await db.refresh(db_todo)
    return db_todo


async def update_todo(db: AsyncSession, *, db_todo: Todo, todo_in: TodoUpdate) -> Todo:
    update_data = todo_in.model_dump(exclude_unset=True)
    if not update_data:
        return db_todo

    stmt = (
        update(Todo)
        .where(Todo.id == db_todo.id)
        .values(**update_data)
        .execution_options(synchronize_session="fetch")
    )
    await db.execute(stmt)
    await db.flush()
    await db.refresh(db_todo)
    return db_todo


async def delete_todo(
    db: AsyncSession, *, todo_id: int, owner_id: int
) -> Optional[Todo]:
    db_todo = await get_todo(db=db, todo_id=todo_id, owner_id=owner_id)
    if not db_todo:
        return None

    stmt = delete(Todo).where(Todo.id == todo_id)
    await db.execute(stmt)
    await db.flush()
    return db_todo
