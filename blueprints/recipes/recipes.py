from flask import Blueprint,request,make_response,jsonify
from bson import ObjectId
from decorators import jwt_required,admin_required
import globals
from datetime import datetime, timezone

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
        if 'created_by' in recipe:
         recipe['created_by'] = str(recipe['created_by'])

        if 'reviews' in recipe and isinstance(recipe['reviews'], list):
         for review in recipe['reviews']:
           if '_id' in review:
             review['_id'] = str(review['_id']) 
              
        return make_response(jsonify(recipe), 200)
    else:
        return make_response(jsonify({"error": "Recipe not found"}), 404)


@recipes_bp.route("/api/v1.0/recipes", methods=["POST"])
@jwt_required
def add_recipe():
    required_fields = ['Title', 'Ingredients', 'Instructions','Cleaned_Ingredients']

    missing = [f for f in required_fields if not request.form.get(f, "").strip()]
    if missing:
        return make_response(jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400)
     
     
    if all(field in request.form for field in required_fields):
        # Get Ingredients
        ingredients_raw = request.form.getlist("Ingredients") or request.form.get("Ingredients", "").split(",")
        ingredients_list = [i.strip() for item in ingredients_raw for i in item.split(",") if i.strip()]

        # Get Cleaned Ingredients
        cleaned_raw = request.form.getlist("Cleaned_Ingredients") or request.form.get("Cleaned_Ingredients", "").split(",")
        cleaned_ingredients_list = [i.strip() for item in cleaned_raw for i in item.split(",") if i.strip()]

         
        new_recipe = {
            "Title": request.form["Title"],
            "Ingredients":ingredients_list,
            "Instructions": request.form["Instructions"],
            "Image_Name": request.form.get("Image_Name", ""),  
            "Cleaned_Ingredients": cleaned_ingredients_list,
            "num_ingredients": len(cleaned_ingredients_list),
            "reviews": [],
            "created_by": ObjectId(request.user_id)
  
       }

        new_recipe_id = collection.insert_one(new_recipe)
        new_recipe_link = "http://localhost:5000/api/v1.0/recipes/" + str(new_recipe_id.inserted_id)
        return make_response(jsonify({"url": new_recipe_link}), 201)

    else:
        return make_response(jsonify({"error": "Missing required form data"}), 400)
    
@recipes_bp.route("/api/v1.0/recipes/<string:id>", methods=["PUT"])
@jwt_required
def edit_recipes(id):

    required_fields = ['Title', 'Ingredients', 'Instructions','Cleaned_Ingredients']

    missing = [f for f in required_fields if not request.form.get(f, "").strip()]
    if missing:
        return make_response(jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400)
    
    recipe = collection.find_one({"_id": ObjectId(id)})
    if not recipe:
        return make_response(jsonify({"error": "Recipe not found"}), 404)
    
    if str(recipe.get("created_by")) != request.user_id and not request.is_admin:
        return make_response(jsonify({"error": "Not authorized"}), 403)

     
    ingredients_raw = request.form.getlist("Ingredients") or request.form.get("Ingredients", "").split(",")
    ingredients_list = [i.strip() for item in ingredients_raw for i in item.split(",") if i.strip()]

    cleaned_raw = request.form.getlist("Cleaned_Ingredients") or request.form.get("Cleaned_Ingredients", "").split(",")
    cleaned_ingredients_list = [i.strip() for item in cleaned_raw for i in item.split(",") if i.strip()]


    
    if all(field in request.form for field in required_fields):
        result = collection.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "Title": request.form["Title"],
                    "Ingredients":ingredients_list,
                    "Instructions": request.form["Instructions"],
                    "Image_Name": request.form.get("Image_Name", ""),
                    "Cleaned_Ingredients":  cleaned_ingredients_list,
                    "num_ingredients": len(cleaned_ingredients_list),
                    "reviews": [],
                 
                    
                    
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
 
def delete_recipe(id):
    recipe = collection.find_one({"_id":ObjectId(id)})
    if not recipe:
        return make_response(jsonify({"error": "Recipe not found"}),404)
    print("Recipe created_by:", str(recipe.get("created_by")))
    print("JWT user_id:", request.user_id)
    print("Is admin:", request.is_admin)

    if str(recipe.get("created_by")) != str(request.user_id) and not request.is_admin:
        return make_response(jsonify({"error": "Not authorized"}),403)
    result = collection.delete_one({"_id": recipe["_id"]})
    if result.deleted_count == 1:
        return make_response(jsonify({"message": "Recipe deleted"}),200)
 

   


@recipes_bp.route("/api/v1.0/recipes/search", methods=["GET"])
def search_by_title_and_ingredients():
    query = request.args.get("q", "").strip()

    if not query:
        return make_response(jsonify({"error": "Missing search query"}), 400)

    # Aggregation pipeline to search in title and ingredients
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"Title": {"$regex": query, "$options": "i"}},  # search in title
                    {"Cleaned_Ingredients": {
                        "$elemMatch": {"$regex": query, "$options": "i"}}}  # search in ingredients
                ]
            }
        },
        {"$limit": 20}  # optional limit
    ]

    results = list(collection.aggregate(pipeline))

    # Convert ObjectId to string
    for recipe in results:
        recipe["_id"] = str(recipe["_id"])
        if "reviews" in recipe:
            for review in recipe["reviews"]:
                if "_id" in review:
                    review["_id"] = str(review["_id"])

    return make_response(jsonify(results), 200)


@recipes_bp.route("/api/v1.0/recipes/searchByNum", methods=["GET"])
def searchByNumOfIngredients():
    query = request.args.get("q", "").strip()

    if not query:
        return make_response(jsonify({"error": "Missing search query"}), 400)

    if not query.isdigit():
        return make_response(jsonify({"error": "Query must be a number"}), 400)

    number = int(query)
    pipeline = [{ "$match": { "num_ingredients": { "$eq": number }}}]

    results = list(collection.aggregate(pipeline))
    for recipe in results:
        recipe["_id"] = str(recipe["_id"])
        if "reviews" in recipe:
            for review in recipe["reviews"]:
                if "_id" in review:
                    review["_id"] = str(review["_id"])

    return make_response(jsonify(results), 200)

@recipes_bp.route("/api/v1.0/recipes/mostIngredients", methods=["GET"])
def recipes_with_most_ingredients():
    pipeline = [
        {"$sort": {"num_ingredients": -1}},
        {"$limit": 1}  # change to 5 if you want top 5
    ]

    results = list(collection.aggregate(pipeline))

    # Convert ObjectId to string for JSON
    for recipe in results:
        recipe["_id"] = str(recipe["_id"])
        if "reviews" in recipe:
            for review in recipe["reviews"]:
                if "_id" in review:
                    review["_id"] = str(review["_id"])

    return make_response(jsonify(results), 200)

    
@recipes_bp.route("/api/v1.0/recipes/ingredients/top5", methods=["GET"])
def top_5_ingredients():

    pipeline = [
    {"$unwind": "$Cleaned_Ingredients"},
    {"$match": {"Cleaned_Ingredients": {"$nin": ["divided", "chopped", "peeled", "finely chopped", "thinly sliced"]}}},
    {"$group": {"_id": "$Cleaned_Ingredients", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 5}
]

    results = list(collection.aggregate(pipeline))

    # Rename _id to ingredient for clarity
    for item in results:
        item["ingredient"] = item.pop("_id")

    return make_response(jsonify(results), 200)


 