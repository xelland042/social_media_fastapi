from pydantic import BaseModel


class Post(BaseModel):
    title: str
    content: str
    author: str


class CreatePost(BaseModel):
    title: str
    content: str


class CreateLikePost(BaseModel):
    post_id: str
    author_id: str


class CreateComment(BaseModel):
    text: str
