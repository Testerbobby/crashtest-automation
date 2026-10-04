from typing import Optional
from pydantic import BaseModel

class ProfileModel(BaseModel):
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    following: bool

class ProfileResponse(BaseModel):
    profile: ProfileModel
