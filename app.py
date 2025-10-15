from flask import Flask, request, jsonify,make_response
import pandas as pd
from pymongo import MongoClient
from bson import ObjectId 

app = Flask(__name__)
client = MongoClient("mongodb://127.0.0.1:27017")
db = client["recipeDB"]        
collection = db["recipes"] 

 
# Load CSV and insert into MongoDB if empty
df = pd.read_csv("recipe.csv")

 

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
def show_one_recipe(id):
    recipe = collection.find_one({'_id': ObjectId(id)})
    if recipe is not None:
        recipe['_id'] = str(recipe['_id'])   
        
        return make_response(jsonify(recipe), 200)
    else:
        return make_response(jsonify({"error": "Recipe not found"}), 404)


@app.route("/api/v1.0/recipes", methods=["POST"])
def add_recipe():
    required_fields = ['Title', 'Ingredients', 'Instructions']

    # Check if all required fields are present
    if all(field in request.form for field in required_fields):
        new_recipe = {
            "Title": request.form["Title"],
            "Ingredients": request.form["Ingredients"],
            "Instructions": request.form["Instructions"],
            "Image_Name": request.form.get("Image_Name", ""),  
            "Cleaned_Ingredients": request.form.get("Cleaned_Ingredients", ""),
            "Rating":request.form.get("Rating", ""),
            "Review":request.form.get("Review", ""),
               
        }

        new_recipe_id = collection.insert_one(new_recipe)
        new_recipe_link = "http://localhost:5000/api/v1.0/recipes/" + str(new_recipe_id.inserted_id)
        return make_response(jsonify({"url": new_recipe_link}), 201)

    else:
        return make_response(jsonify({"error": "Missing required form data"}), 400)
    
@app.route("/api/v1.0/recipes/<string:id>", methods=["DELETE"])
def delete_recipe(id):
    result = collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return make_response(jsonify({}), 204)
    else:
        return make_response(jsonify({"error": "Invalid business ID"}), 404)

 
if __name__ == "__main__":
    app.run(debug=True)
 

 