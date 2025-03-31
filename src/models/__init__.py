from pydantic import BaseModel, Field
from typing import Callable, Any, List, Set, Literal, Optional
import uuid

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    handle: Callable[..., Any]
    args: List[Any]

class Proxy(BaseModel):
    ip: str
    port: int
    protocol: List[Literal["http", "https", "socks4", "socks5"]]
    username: Optional[str] = None
    password: Optional[str] = None
    responseTime: float
    countryCode: Optional[str] = None



