from typing import Optional, List
from pydantic import BaseModel, Field
from src.models.profile import ProfileModel

class ArticleModel(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    body: Optional[str] = None
    tagList: List[str] = Field(default_factory=list)
    createdAt: str
    updatedAt: str
    favorited: bool = False
    favoritesCount: int = 0
    author: ProfileModel

class SingleArticleResponse(BaseModel):
    article: ArticleModel

class MultipleArticlesResponse(BaseModel):
    articles: List[ArticleModel]
    articlesCount: int
