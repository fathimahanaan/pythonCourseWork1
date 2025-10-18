from flask import Flask, request, jsonify,make_response
import pandas as pd
from pymongo import MongoClient
from bson import ObjectId 
import jwt
import datetime
from functools import wraps
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
client = MongoClient("mongodb://127.0.0.1:27017")
db = client.recipeDB    
collection = db.recipes
users = db.users
blacklist = db.blacklist
 
# Load CSV and insert into MongoDB if empty
df = pd.read_csv("recipe.csv")

def jwt_required(func):
    @wraps(func) #please pass token in header not in params
    def jwt_required_wrapper(*args,**kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return make_response(jsonify({'message':'Token is missing'}),401)
        try:
            data = jwt.decode(token,app.config['SECRET_KEY'],algorithms='HS256')
       
        except:
            return make_response(jsonify({'message':'Token is invalid'}),401)
        bl_token = blacklist.find_one({'token':token})
        if bl_token is not None:
            return make_response(jsonify({'message':'Token has been cancelled'}),401)
        return func(*args,**kwargs)
    return jwt_required_wrapper

def admin_required(func):
    @wraps(func)
    def admin_required_wrapper(*args,**kwargs):
        token = request.headers['x-access-token']
        data = jwt.decode (token, app.config['SECRET_KEY'],algorithms=['HS256'])
        if data['admin']:
            return func(*args,**kwargs)
        else:
            return make_response(jsonify({'message':'Admin access required'}),401)
    return admin_required_wrapper


@app.route("/api/v1.0/recipes", methods=['GET'])
def show_all_recipes():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))

    page_start = page_size * (page_num - 1)
    data_to_return = []

    for recipe in collection.find().skip(page_start).limit(page_size):
        recipe['_id'] = str(recipe['_id'])

        # Convert review ObjectId if reviews exist
        if 'reviews' in recipe and isinstance(recipe['reviews'], list):
            for review in recipe['reviews']:
                if '_id' in review:
                    review['_id'] = str(review['_id'])

        data_to_return.append(recipe)

    return make_response(jsonify(data_to_return), 200)

    

@app.route("/api/v1.0/recipes/<string:id>", methods=['GET'])   
@jwt_required #jwt implemeted
def show_one_recipe(id):
    recipe = collection.find_one({'_id': ObjectId(id)})
    if recipe is not None:
        recipe['_id'] = str(recipe['_id'])  
        for review in recipe['reviews']:
           review['_id'] = str(review['_id']) 
        
        return make_response(jsonify(recipe), 200)
    else:
        return make_response(jsonify({"error": "Recipe not found"}), 404)


@app.route("/api/v1.0/recipes", methods=["POST"])
@jwt_required
def add_recipe():
    required_fields = ['Title', 'Ingredients', 'Instructions']

     
    if all(field in request.form for field in required_fields):
        new_recipe = {
            "Title": request.form["Title"],
            "Ingredients": request.form["Ingredients"],
            "Instructions": request.form["Instructions"],
            "Image_Name": request.form.get("Image_Name", ""),  
            "Cleaned_Ingredients": request.form.get("Cleaned_Ingredients", ""),
            "Rating":request.form.get("Rating", ""),
            
               
        }

        new_recipe_id = collection.insert_one(new_recipe)
        new_recipe_link = "http://localhost:5000/api/v1.0/recipes/" + str(new_recipe_id.inserted_id)
        return make_response(jsonify({"url": new_recipe_link}), 201)

    else:
        return make_response(jsonify({"error": "Missing required form data"}), 400)
    
@app.route("/api/v1.0/recipes/<string:id>", methods=["PUT"])
@jwt_required
def edit_recipes(id):
    required_fields = ['Title', 'Ingredients', 'Instructions']

    
    if all(field in request.form for field in required_fields):
        result = collection.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "Title": request.form["Title"],
                    "Ingredients": request.form["Ingredients"],
                    "Instructions": request.form["Instructions"],
                    "Image_Name": request.form.get("Image_Name", ""),
                    "Cleaned_Ingredients": request.form.get("Cleaned_Ingredients", ""),
                    "Rating": request.form.get("Rating", ""),
                    
                }
            }
        )

 
        if result.matched_count == 1:
            edited_recipe_link = f"http://localhost:5000/api/v1.0/recipes/{id}"
            return make_response(jsonify({"url": edited_recipe_link}), 200)
        else:
            return make_response(jsonify({"error": "Invalid recipe ID"}), 404)

    else:
        return make_response(jsonify({"error": "Missing required form data"}), 400)
  

@app.route("/api/v1.0/recipes/<string:id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_recipe(id):
    result = collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return make_response(jsonify({}), 204)
    else:
        return make_response(jsonify({"error": "Invalid recipe ID"}), 404)

#review
@app.route("/api/v1.0/recipes/<string:id>/reviews", methods=["POST"])
def add_new_review(id):
    new_review = {
        "_id": ObjectId(),
        "username": request.form["username"],
        "comment": request.form["comment"],
        "stars": request.form["stars"]
    }

    result = collection.update_one(
        {"_id": ObjectId(id)},
        {"$push": {"reviews": new_review}}
    )

    if result.matched_count == 1:
        new_review_link = (
            "http://localhost:5000/api/v1.0/recipe/"
            + id + "/reviews/" + str(new_review["_id"])
        )
        return make_response(jsonify({"url": new_review_link}), 201)
    else:
        return make_response(jsonify({"error": "Invalid recipe ID"}), 404)

@app.route('/api/v1.0/login', methods=['GET'])
def login():
    auth = request.authorization

    if auth:
        user = users.find_one({'username': auth.username})
        if user is not None:
            if bcrypt.checkpw(bytes(auth.password, 'UTF-8'), user['password']):
                token = jwt.encode({
                    'user': auth.username,
                    'admin':user['admin'],
                    'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=30)
                }, app.config['SECRET_KEY'], algorithm='HS256')

                return make_response(jsonify({'token': token}), 200)
            else:
                return make_response(jsonify({'Message': 'Bad password'}), 401)
        else:
            return make_response(jsonify({'Message': 'Bad username'}), 401)

    return make_response(jsonify({'message': 'Authentication required'}), 401)

@app.route('/api/v1.0/logout', methods=['GET'])
@jwt_required
def logout():
    token = request.headers['x-access-token']
    blacklist.insert_one({'token':token})
    return make_response(jsonify({'message':'Logout successful'}),200)

if __name__ == "__main__":
    app.run(debug=True)
 

 