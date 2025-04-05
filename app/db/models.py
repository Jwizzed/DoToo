from typing import Optional
from datetime import datetime, date

from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    todos: Mapped[list["Todo"]] = relationship(
        "Todo", back_populates="owner", cascade="all, delete-orphan"
    )


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(
        String, index=True, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String, default="Not Started", nullable=False
    )  # "Not Started", "In Progress", "Done"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    photo_filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    priority: Mapped[int] = mapped_column(
        Integer, default=2, nullable=True, index=True
    )  # 1: High, 2: Medium, 3: Low

    owner: Mapped["User"] = relationship("User", back_populates="todos")
