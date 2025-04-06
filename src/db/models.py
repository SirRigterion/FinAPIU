from typing import Optional
from sqlalchemy import Column, ForeignKey, String, Integer, Boolean, TIMESTAMP, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SAEnum
from datetime import datetime
from src.db.database import Base
from src.task.enums import TaskPriority, TaskStatus

# Пользователи
class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), default=1)
    registered_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    completed_tasks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tasks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    edited_articles_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    shift: Mapped[str] = mapped_column(String(50), nullable=False, comment="Текущая смена пользователя")
    
    authored_tasks = relationship("Task", back_populates="author", foreign_keys="Task.author_id")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")

# Роли
class Role(Base):
    __tablename__ = "roles"
    
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)

# Статьи
class Article(Base):
    __tablename__ = "articles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(String(5000), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    
    images = relationship("ArticleImage", back_populates="article", lazy="selectin", cascade="all, delete-orphan")
    history = relationship("ArticleHistory", back_populates="article", cascade="all, delete-orphan")

class ArticleImage(Base):
    __tablename__ = "article_images"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    
    article = relationship("Article", back_populates="images")

class ArticleHistory(Base):
    __tablename__ = "article_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    event: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    old_title: Mapped[Optional[str]] = mapped_column(String(255))
    new_title: Mapped[Optional[str]] = mapped_column(String(255))
    old_content: Mapped[Optional[str]] = mapped_column(String(5000))
    new_content: Mapped[Optional[str]] = mapped_column(String(5000))
    
    article = relationship("Article", back_populates="history")

# Задачи
class Task(Base):
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(5000))
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=TaskStatus.ACTIVE
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=TaskPriority.MEDIUM
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    image_paths: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    
    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")
    author = relationship("User", back_populates="authored_tasks", foreign_keys=[author_id])
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])

class TaskHistory(Base):
    __tablename__ = "task_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    event: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(500))
    changed_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    task = relationship("Task", back_populates="history")