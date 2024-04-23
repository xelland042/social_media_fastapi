from pydantic import BaseModel


class Room(BaseModel):
    user_1: str
    user_2: str
