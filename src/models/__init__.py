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

    def parse(self):
        proxy_config = {
            "server": f"{next(iter(self.protocol))}://{self.ip}:{self.port}"
        }
            
        if self.username and self.password:
            proxy_config.update({
                "username": self.username,
                "password": self.password
            })
        return proxy_config


    def __hash__(self):
        return hash((self.ip, self.port))

    # def __eq__(self, other):
    #     if not isinstance(other, Proxy):
    #         return False
    #     return self.ip == other.ip and self.port == other.port
