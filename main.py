from fastapi import FastAPI
from user_app.views import router as user_router
from post_app.views import router as posts_router
from chat_app.views import router as chat_router

app = FastAPI()

app.include_router(user_router, prefix="/user")
app.include_router(posts_router, prefix="/posts")
app.include_router(chat_router, prefix='/chat')
