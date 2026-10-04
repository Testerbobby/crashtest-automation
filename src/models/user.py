from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class UserModel(BaseModel):
    email: str
    token: str
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None

class UserResponse(BaseModel):
    user: UserModel

class GenericErrorModel(BaseModel):
    errors: Dict[str, Any] = Field(default_factory=dict)
