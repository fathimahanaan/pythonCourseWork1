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
    {"name": "Fathima Hanaan", "username": "hanaan", "email": "hanaan@example.com", "password": "hii", "admin": False, "favorites": []},
    {"name": "Stephanie", "username": "stephie", "email": "stephie@example.com", "password": "hello", "admin": False, "favorites": []},
    {"name": "Admin", "username": "admin1", "email": "admin@example.com", "password": "admin123", "admin": True, "favorites": []},
    {"name": "Ashley", "username": "ashley23", "email": "ashley23@example.com", "password": "hello", "admin": False, "favorites": []},
    {"name": "Rachel", "username": "rachel_m", "email": "rachel_m@example.com", "password": "hello", "admin": False, "favorites": []},
    {"name": "Nahrin", "username": "nahrin_k", "email": "nahrin_k@example.com", "password": "hello", "admin": False, "favorites": []},
    {"name": "Kim", "username": "kim", "email": "kim_lee@example.com", "password": "hii", "admin": False, "favorites": []},
    {"name": "Kane", "username": "kane_j", "email": "kane_j@example.com", "password": "hello", "admin": False, "favorites": []},
    {"name": "Harry", "username": "harry", "email": "harry_p@example.com", "password": "hello", "admin": False, "favorites": []},
]

for new_user in user_list:
    new_user["password"] = bcrypt.hashpw(new_user["password"].encode('utf-8'), bcrypt.gensalt())
    
    new_user["active"] = True
    new_user["created_at"] = datetime.datetime.utcnow()
    result = users.insert_one(new_user)
  
 