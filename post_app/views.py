from bson import ObjectId

from fastapi import APIRouter, HTTPException, Depends, Path
from user_app.security import get_current_user
from .models import CreatePost, CreateComment
from user_app.models import User
from db import post_collection, comment_collection, like_collection

router = APIRouter()


@router.post("/", tags=['Posts'])
async def create_post(post: CreatePost, current_user: User = Depends(get_current_user)):
    title = post.title
    content = post.content
    author = current_user['username']
    post_collection.insert_one({'title': title, 'content': content, 'author': author})
    return {"message": "Post created successfully", "post": {'title': title, 'content': content}}


@router.get("/", tags=['Posts'])
async def get_all_posts(current_user: User = Depends(get_current_user)):
    # Check if the user is authenticated
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Retrieve all posts
    posts = post_collection.find({})
    cursor_list = []
    for document in posts:
        # Convert ObjectId to string for serialization
        document['_id'] = str(document['_id'])
        cursor_list.append(document)
    return {"posts": cursor_list}


@router.get("/user/{username}/", tags=['Posts'])
async def get_posts_by_username(username: str, current_user: User = Depends(get_current_user)):
    # Check if the current user is querying their own posts
    if current_user['username'] != username:
        raise HTTPException(status_code=403, detail="You are not authorized to view these posts")

    # Retrieve posts by username
    posts = post_collection.find({"author": username})
    cursor_list = []
    for document in posts:
        # Convert ObjectId to string for serialization
        document['_id'] = str(document['_id'])
        cursor_list.append(document)
    return {"posts": cursor_list}


@router.get("/{post_id}/", tags=['Posts'])
async def get_post_details(post_id: str = Path(...), current_user: User = Depends(get_current_user)):
    author_id = str(current_user['_id'])
    post = post_collection.find_one({"_id": ObjectId(post_id)})
    like = like_collection.find_one({'author_id': author_id, 'post_id': post_id})
    likes = like_collection.count_documents({'post_id': post_id})
    comments = comment_collection.find({'post_id': post_id})
    cursor_list = []
    for document in comments:
        # Convert ObjectId to string for serialization
        document['_id'] = str(document['_id'])
        cursor_list.append(document)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Convert ObjectId to string for serialization
    post['_id'] = str(post['_id'])
    return {"post": post, 'like': bool(like is not None), 'likes': likes, 'comments': cursor_list}


@router.delete("/{post_id}/", tags=['Posts'])
async def delete_post(post_id: str = Path(...), current_user: User = Depends(get_current_user)):
    # Check if the post exists
    post = post_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if the current user is the author of the post
    if current_user['username'] != post["author"]:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this post")

    # Delete the post
    post_collection.delete_one({"_id": ObjectId(post_id)})

    return {"message": "Post deleted successfully"}


@router.post("/{post_id}/add-comment/", tags=['Posts'])
async def add_comment(comment_text: CreateComment, post_id: str = Path(...),
                      current_user: User = Depends(get_current_user)):
    post = post_collection.find_one({'_id': post_id})
    if current_user and post:
        author_id = str(current_user['_id'])
        comment_data = {'author_id': author_id, 'post_id': post_id, 'text': comment_text.text}
        comment_collection.insert_one(comment_data)
        return {'user': current_user['username'], 'text': comment_text.text}


@router.post('/{post_id}/like/', tags=['Posts'])
async def add_remove_like(post_id: str = Path(...), current_user: User = Depends(get_current_user)):
    author_id = str(current_user['_id'])
    post = post_collection.find_one({'_id': ObjectId(post_id)})
    like = {'author_id': author_id, 'post_id': post_id}
    exist_like = like_collection.find_one(like)
    if current_user and exist_like and post:
        like_collection.delete_one(like)
        return {'message': 'Like removed!', 'author': current_user['username'], 'post_id': post_id}
    elif current_user and post and exist_like is None:
        like_collection.insert_one(like)
        return {'message': 'Liked', 'author': current_user['username'], 'post_id': post_id}
    else:
        return {'message': 'Something went wrong!'}
