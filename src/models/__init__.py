from pydantic import BaseModel, Field
from typing import Callable, Any, List
import uuid

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    handle: Callable[..., Any]
    args: List[Any]

