from typing import List, Optional

from sqlalchemy import update, delete, asc, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Todo
from app.schemas.todo import TodoCreate, TodoUpdate


async def get_todos_by_owner(
    db: AsyncSession,
    owner_id: int,
    skip: int = 0,
    limit: int = 100,
    filter_status: Optional[str] = None,
    filter_priority: Optional[int] = None,
    sort_by: str = "created_at",
    search_term: Optional[str] = None,
) -> List[Todo]:
    """
    Get todos for a specific owner with filtering, sorting, and searching.
    """
    stmt = select(Todo).filter(Todo.owner_id == owner_id)

    if filter_status:
        stmt = stmt.filter(Todo.status == filter_status)
    if filter_priority is not None:
        stmt = stmt.filter(Todo.priority == filter_priority)

    if search_term:
        search_pattern = f"%{search_term}%"
        stmt = stmt.filter(
            or_(
                Todo.title.ilike(search_pattern), Todo.description.ilike(search_pattern)
            )
        )

    sort_column = Todo.created_at
    sort_direction = desc

    if sort_by == "due_date_asc":
        sort_column = Todo.due_date
        sort_direction = asc
    elif sort_by == "due_date_desc":
        sort_column = Todo.due_date
        sort_direction = desc
    elif sort_by == "priority_asc":
        sort_column = Todo.priority
        sort_direction = asc
    elif sort_by == "priority_desc":
        sort_column = Todo.priority
        sort_direction = desc
    elif sort_by == "created_at_asc":
        sort_column = Todo.created_at
        sort_direction = asc

    stmt = stmt.order_by(sort_direction(sort_column))

    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
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
    photo_filename: Optional[str] = None,
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
        .where(Todo.id == db_todo.id, Todo.owner_id == db_todo.owner_id)
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

    stmt = delete(Todo).where(Todo.id == todo_id, Todo.owner_id == owner_id)
    await db.execute(stmt)
    await db.flush()

    return db_todo
