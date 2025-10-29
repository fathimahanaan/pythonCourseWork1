from pymongo import MongoClient
import bcrypt
import datetime


# Connect to MongoDB
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.recipeDB
users  = db.users
users.delete_many({})  # Clear existing users

# User list
user_list = [
    {"name": "Fathima Hanaan", "username": "hanaan", "email": "hanaan@example.com", "password": "hii", "admin": False},
    {"name": "John Doe", "username": "johnd", "email": "john.doe@example.com", "password": "hello", "admin": False},
    {"name": "Site Admin", "username": "admin1", "email": "admin@example.com", "password": "admin123", "admin": True}
]

for new_user in user_list:
    new_user["password"] = bcrypt.hashpw(new_user["password"].encode('utf-8'), bcrypt.gensalt())
    new_user["active"] = True
    new_user["created_at"] = datetime.datetime.utcnow()
    result = users.insert_one(new_user)
  
 