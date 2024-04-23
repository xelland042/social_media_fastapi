from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Path, WebSocket, WebSocketDisconnect
from user_app.security import get_current_user
from user_app.models import User
from .managers import ConnectionManager
from db import chat_collection, users_collection, message_collection

router = APIRouter()

manager = ConnectionManager()


@router.post('/{username}/start-chat', tags=['Chats'])
async def start_chat_with_user(username=Path(...), current_user: User = Depends(get_current_user)):
    user = users_collection.find_one({'username': username})
    data = {
        'user_1': str(current_user['_id']),
        'username_1': str(current_user['username']),
        'user_2': str(user['_id']),
        'username_2': str(user['username'])
    }
    chat_collection.insert_one(data)
    return {'message': f'You started chat with {username}'}


@router.get('/chats/', tags=['Chats'])
async def get_my_chats(current_user: User = Depends(get_current_user)):
    started_me = [{'_id': str(i['_id']), 'username': i['username_2']} for i in
                  chat_collection.find({'user_1': str(current_user['_id'])})]
    started_user = [{'_id': str(i['_id']), 'username': i['username_1']} for i in
                    chat_collection.find({'user_2': str(current_user['_id'])})]
    return {'started_me': started_me, 'started_user': started_user}


async def save_message(room_id, message, username):
    data = {'room_id': room_id, 'message': message, 'username': username}
    message_collection.insert_one(data)


@router.websocket('/room/{room_id}/')
async def chat_with_user(websocket: WebSocket, room_id=Path(...)):
    await manager.connect(websocket)
    token = websocket.headers['Authorization'].split(' ')[1]
    user = get_current_user(token)
    try:
        while True:
            msg = await websocket.receive_text()
            await manager.send_message(f'{user["username"]}: {msg}')
            await save_message(room_id, msg, user['username'])
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.send_message("Have a great day!")
