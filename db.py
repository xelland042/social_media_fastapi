from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["mydatabase"]
users_collection = db["users"]
post_collection = db["posts"]
like_collection = db["likes"]
comment_collection = db["comments"]
follower_collection = db["followers"]
chat_collection = db["chats"]
message_collection = db["messages"]
