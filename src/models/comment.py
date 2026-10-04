from typing import List, Optional
from pydantic import BaseModel
from src.models.profile import ProfileModel

class CommentModel(BaseModel):
    id: str
    createdAt: str
    updatedAt: Optional[str] = None
    body: str
    author: ProfileModel

class SingleCommentResponse(BaseModel):
    comment: CommentModel

class MultipleCommentsResponse(BaseModel):
    comments: List[CommentModel]
