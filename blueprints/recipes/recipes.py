from flask import Blueprint,request,make_response,jsonify
from bson import ObjectId
from decorators import jwt_required,admin_required
import globals

recipes_bp = Blueprint("recipes_bp",__name__)

collection = globals.db.recipes

@recipes_bp.route("/api/v1.0/recipes", methods=['GET'])
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

    

@recipes_bp.route("/api/v1.0/recipes/<string:id>", methods=['GET'])   
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


@recipes_bp.route("/api/v1.0/recipes", methods=["POST"])
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
    
@recipes_bp.route("/api/v1.0/recipes/<string:id>", methods=["PUT"])
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
  

@recipes_bp.route("/api/v1.0/recipes/<string:id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_recipe(id):
    result = collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return make_response(jsonify({"message": "Recipe deleted"}), 204)
    else:
        return make_response(jsonify({"error": "Invalid recipe ID"}), 404)

 