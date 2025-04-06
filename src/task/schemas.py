from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from src.task.enums import TaskStatus, TaskPriority
from src.user.schemas import UserInfo
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from src.task.enums import TaskStatus, TaskPriority
from src.user.schemas import UserInfo

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    assignee_id: int
    image_paths: Optional[List[str]] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    author: UserInfo
    assignee: UserInfo
    created_at: datetime
    updated_at: datetime
    image_paths: List[str] = []

    class Config:
        orm_mode = True

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    image_paths: Optional[List[str]] = None

class ReassignTaskRequest(BaseModel):
    new_assignee_id: int
    comment: Optional[str] = None

class TaskHistoryResponse(BaseModel):
    event: str
    changed_at: datetime
    user_id: int
    old_status: Optional[TaskStatus] = None
    new_status: Optional[TaskStatus] = None

    class Config:
        orm_mode = True