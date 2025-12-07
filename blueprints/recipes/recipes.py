from flask import Blueprint,request,make_response,jsonify
from bson import ObjectId
from decorators import jwt_required,admin_required
import globals
from datetime import datetime, timezone

recipes_bp = Blueprint("recipes_bp",__name__)

collection = globals.db.recipes
users  = globals.db.users

# show all recipe
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

     
        if 'reviews' in recipe and isinstance(recipe['reviews'], list):
            for review in recipe['reviews']:
                if '_id' in review:
                    review['_id'] = str(review['_id'])

        data_to_return.append(recipe)

    return make_response(jsonify(data_to_return), 200)

    
#show one recipe
@recipes_bp.route("/api/v1.0/recipes/<string:id>", methods=['GET'])   
 
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

#add recipe
@recipes_bp.route("/api/v1.0/recipes", methods=["POST"])
  
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
               # add user who created
            
  
       }

        new_recipe_id = collection.insert_one(new_recipe)
        new_recipe_link = "http://localhost:5000/api/v1.0/recipes/" + str(new_recipe_id.inserted_id)
        return make_response(jsonify({"url": new_recipe_link}), 201)

    else:
        return make_response(jsonify({"error": "Missing required form data"}), 400)

#edit recipe   
@recipes_bp.route("/api/v1.0/recipes/<string:id>", methods=["PUT"])
@jwt_required
@admin_required
def edit_recipes(id):
    required_fields = ['Title', 'Ingredients', 'Instructions', 'Cleaned_Ingredients']

    # Check for missing fields
    missing = [f for f in required_fields if not request.form.get(f, "").strip()]
    if missing:
        return make_response(jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400)

    # Find the recipe
    recipe = collection.find_one({"_id": ObjectId(id)})
    if not recipe:
        return make_response(jsonify({"error": "Recipe not found"}), 404)

    # Process ingredients
    ingredients_raw = request.form.getlist("Ingredients") or request.form.get("Ingredients", "").split(",")
    ingredients_list = [i.strip() for item in ingredients_raw for i in item.split(",") if i.strip()]

    cleaned_raw = request.form.getlist("Cleaned_Ingredients") or request.form.get("Cleaned_Ingredients", "").split(",")
    cleaned_ingredients_list = [i.strip() for item in cleaned_raw for i in item.split(",") if i.strip()]

    # Update recipe
    result = collection.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "Title": request.form["Title"],
                "Ingredients": ingredients_list,
                "Instructions": request.form["Instructions"],
                "Image_Name": request.form.get("Image_Name", ""),
                "Cleaned_Ingredients": cleaned_ingredients_list,
                "num_ingredients": len(cleaned_ingredients_list),
                "reviews": recipe.get("reviews", []),  # keep existing reviews
            }
        }
    )

    if result.matched_count == 1:
        edited_recipe_link = f"http://localhost:5000/api/v1.0/recipes/{id}"
        return make_response(jsonify({"url": edited_recipe_link}), 200)
    else:
        return make_response(jsonify({"error": "Invalid recipe ID"}), 404)
    

@recipes_bp.route("/api/v1.0/recipes/<string:id>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_recipe(id):
    
    try:
        result = collection.delete_one({"_id": ObjectId(id)})
        
        if result.deleted_count == 0:
            return make_response(jsonify({"error": "Recipe not found"}), 404)
        
        return make_response(jsonify({"message": "Recipe deleted"}), 200)
    
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
 

   

#search recipe by title and ingredients
@recipes_bp.route("/api/v1.0/recipes/search", methods=["GET"])
 
def search_by_title_and_ingredients():
    query = request.args.get("q", "").strip()

    if not query:
        return make_response(jsonify({"error": "Missing search query"}), 400)

     
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

   
    for recipe in results:
        recipe["_id"] = str(recipe["_id"])
        if "reviews" in recipe:
            for review in recipe["reviews"]:
                if "_id" in review:
                    review["_id"] = str(review["_id"])

    return make_response(jsonify(results), 200)

#search by num of ingredients
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

#searcch by most ingredients
@recipes_bp.route("/api/v1.0/recipes/mostIngredients", methods=["GET"])
 
def recipes_with_most_ingredients():
    pipeline = [
        {"$sort": {"num_ingredients": -1}},
        {"$limit": 1}  
    ]

    results = list(collection.aggregate(pipeline))

     
    for recipe in results:
        recipe["_id"] = str(recipe["_id"])
        if "reviews" in recipe:
            for review in recipe["reviews"]:
                if "_id" in review:
                    review["_id"] = str(review["_id"])

    return make_response(jsonify(results), 200)

#get top 5 ingredients   
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

   
    for item in results:
        item["ingredient"] = item.pop("_id")

    return make_response(jsonify(results), 200)

#get recipe pages
@recipes_bp.route("/api/v1.0/recipes/pages", methods=["GET"])
def get_recipe_pages():
     page_size = int(request.args.get("ps", 10))
     total_recipes = collection.count_documents({})

     total_pages = (total_recipes + page_size - 1) // page_size 
     return make_response(jsonify({
        "total_recipes": total_recipes,
        "page_size": page_size,
        "total_pages": total_pages
        }),200)
 #recipe add to favorites

@recipes_bp.route("/api/v1.0/recipes/favorites", methods=["POST"])
@jwt_required
def add_favorite():

    recipe_id = request.form.get("recipe_id") or request.json.get("recipe_id")
    
    if not recipe_id:
        return make_response(jsonify({"error": "Recipe ID is required"}), 400)
    
    recipe = collection.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        return make_response(jsonify({"error": "Recipe not found"}), 404)
    
    result = users.update_one(
        {"_id": ObjectId(request.user_id)},
        {"$addToSet": {"favorites": ObjectId(recipe_id)}}  
    )
    
    if result.modified_count == 1:
        return make_response(jsonify({"message": "Recipe added to favorites"}), 200)
    else:
        return make_response(jsonify({"message": "Recipe already in favorites"}), 200)

@recipes_bp.route("/api/v1.0/recipes/favorites", methods=["GET"])
@jwt_required
def get_favorites():
    # Find logged-in user
    user = users.find_one({"_id": ObjectId(request.user_id)})

    if not user:
        return make_response(jsonify({"error": "User not found"}), 404)

    # Get array of ObjectId recipe IDs
    favorite_ids = user.get("favorites", [])

    if not favorite_ids:
        return make_response(jsonify([]), 200)

    # Fetch all recipes whose IDs are in favorites
    favorite_recipes = list(collection.find(
        {"_id": {"$in": favorite_ids}}
    ))

    # Convert ObjectIds to strings for JSON
    for recipe in favorite_recipes:
        recipe["_id"] = str(recipe["_id"])

        if "reviews" in recipe:
            for review in recipe["reviews"]:
                if "_id" in review:
                    review["_id"] = str(review["_id"])

    return make_response(jsonify(favorite_recipes), 200)

@recipes_bp.route("/api/v1.0/recipes/favorites/<string:recipe_id>", methods=["DELETE"])
@jwt_required
def remove_favorite(recipe_id):
    # Check if the recipe exists
    recipe = collection.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        return make_response(jsonify({"error": "Recipe not found"}), 404)
    
    # Remove recipe from user's favorites
    result = users.update_one(
        {"_id": ObjectId(request.user_id)},       # or g.user_id if you switch to g
        {"$pull": {"favorites": ObjectId(recipe_id)}}
    )

    if result.modified_count == 1:
        return make_response(jsonify({"message": "Recipe removed from favorites"}), 200)
    else:
        return make_response(jsonify({"message": "Recipe was not in favorites"}), 200)
