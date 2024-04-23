from bson import ObjectId
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.security import OAuth2PasswordRequestForm

from .security import create_access_token, verify_password, get_password_hash, get_current_user, \
    ACCESS_TOKEN_EXPIRE_MINUTES
from .models import User
from db import users_collection, follower_collection

router = APIRouter()


@router.post("/register/", tags=['Accounts'])
async def register(user_data: User):
    username = user_data.username
    email = user_data.email
    password = user_data.password

    hashed_password = get_password_hash(password)

    users_collection.insert_one(
        {"username": username, "email": email, "hashed_password": hashed_password, "followers": 0, "followings": 0})

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)

    # After saving the user information, you can return username and email
    return {"username": username, "email": email, "access_token": access_token,
            "message": "User registered successfully"}


@router.post("/token/", tags=['Accounts'])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_collection.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.put("/me/", tags=['Accounts'])
async def update_user_profile(user: User, current_user: User = Depends(get_current_user)):
    users_collection.update_one({"username": current_user.username}, {"$set": user.dict()})
    return {"message": "User profile updated successfully"}


@router.delete("/me/", tags=['Accounts'])
async def delete_user(current_user: User = Depends(get_current_user)):
    users_collection.delete_one({"username": current_user.username})
    return {"message": "User deleted successfully"}


@router.get("/me/", tags=['Accounts'])
async def get_user_detail(current_user: User = Depends(get_current_user)):
    current_user['_id'] = str(current_user['_id'])
    followers = follower_collection.count_documents({'user_id': str(current_user['_id'])})
    followings = follower_collection.count_documents({'follower_id': str(current_user['_id'])})
    return {'_id': current_user['_id'], 'username': current_user['username'], 'email': current_user['email'],
            'followers': followers, 'followings': followings}


@router.get('/me/followers', tags=['Accounts'])
async def get_user_followers(current_user: User = Depends(get_current_user)):
    if current_user:
        followers = follower_collection.find({'user_id': str(current_user['_id'])})
        cursor_list = []
        for document in followers:
            temp_user = users_collection.find_one({'_id': ObjectId(document['follower_id'])})
            cursor_list.append({'username': temp_user['username'], 'email': temp_user['email']})
        return cursor_list


@router.get('/me/followings', tags=['Accounts'])
async def get_user_followings(current_user: User = Depends(get_current_user)):
    if current_user:
        followings = follower_collection.find({'follower_id': str(current_user['_id'])})
        cursor_list = []
        for document in followings:
            temp_user = users_collection.find_one({'_id': ObjectId(document['user_id'])})
            cursor_list.append({'username': temp_user['username'], 'email': temp_user['email']})
        return cursor_list


@router.get('/{username}/', tags=['Accounts'])
async def get_user_by_username(username=Path(...), current_user: User = Depends(get_current_user)):
    if current_user:
        user = users_collection.find_one({'username': username})
        user['_id'] = str(user['_id'])
        followers = follower_collection.count_documents({'user_id': str(user['_id'])})
        followings = follower_collection.count_documents({'follower_id': str(user['_id'])})
        return {'username': user['username'], 'email': user['email'], 'followers': followers, 'followings': followings}


@router.get('/{username}/followers', tags=['Accounts'])
async def get_user_followers(username=Path(...), current_user: User = Depends(get_current_user)):
    if current_user:
        user = users_collection.find_one({'username': username})
        followers = follower_collection.find({'user_id': str(user['_id'])})
        cursor_list = []
        for document in followers:
            temp_user = users_collection.find_one({'_id': ObjectId(document['follower_id'])})
            cursor_list.append({'username': temp_user['username'], 'email': temp_user['email']})
        return cursor_list


@router.get('/{username}/followings', tags=['Accounts'])
async def get_user_followings(username=Path(...), current_user: User = Depends(get_current_user)):
    if current_user:
        user = users_collection.find_one({'username': username})
        followings = follower_collection.find({'follower_id': str(user['_id'])})
        cursor_list = []
        for document in followings:
            temp_user = users_collection.find_one({'_id': ObjectId(document['user_id'])})
            cursor_list.append({'username': temp_user['username'], 'email': temp_user['email']})
        return cursor_list


@router.post('/{username}/', tags=['Accounts'])
async def follow_to_user(username=Path(...), current_user: User = Depends(get_current_user)):
    user = users_collection.find_one({'username': username})
    follower_to_user = follower_collection.find_one(
        {'user_id': str(user['_id']), 'follower_id': str(current_user['_id'])})
    if current_user and follower_to_user:
        follower_collection.delete_one({'user_id': str(user['_id']), 'follower_id': str(current_user['_id'])})
        return {'message': f'You have unsubscribed from {user["username"]}'}
    if current_user and follower_to_user is None:
        if str(current_user['_id']) == str(user['_id']):
            return {'message': 'Something went wrong!'}
        follower_collection.insert_one({'user_id': str(user['_id']), 'follower_id': str(current_user['_id'])})
        return {'message': f'You have subscribed {user["username"]}'}
