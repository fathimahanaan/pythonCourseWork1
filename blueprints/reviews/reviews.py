from flask import Blueprint,request,make_response,jsonify
from bson import ObjectId
from bson.errors import InvalidId
from decorators import jwt_required, admin_required
import globals

reviews_bp = Blueprint("reviews_bp",__name__)

collection = globals.db.recipes
 
# add review
@reviews_bp.route("/api/v1.0/recipes/<string:id>/reviews", methods=["POST"])
def add_new_review(id):
    new_review = {
        "_id": str(ObjectId()),  # convert ObjectId to string immediately
        "username": request.form.get("username", ""),
        "comment": request.form.get("comment", ""),
        "stars": int(request.form.get("stars", 0))
    }

    result = collection.update_one(
        {"_id": ObjectId(id)},
        {"$push": {"reviews": new_review}}
    )

    if result.matched_count == 1:
        return make_response(jsonify(new_review), 201)
    else:
        return make_response(jsonify({"error": "Invalid recipe ID"}), 404)
    
             
#get all review
@reviews_bp.route("/api/v1.0/recipes/<string:id>/reviews", methods=["GET"])
def fetch_all_reviews(id):
    data_to_return = []

     
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        return make_response(jsonify({"error": "Invalid recipeID"}), 404)

    
    recipe = collection.find_one(
        {"_id": obj_id},
        {"reviews": 1, "_id": 0}
    )

    if recipe and "reviews" in recipe:
        for review in recipe["reviews"]:
            review["_id"] = str(review["_id"])
            data_to_return.append(review)
        return make_response(jsonify(data_to_return), 200)
    else:
        return make_response(jsonify({"error": "Invalid recipeID"}), 404)

#get single review authentication removd
 
 
 
@reviews_bp.route("/api/v1.0/recipes/<recipe_id>/reviews/<rid>", methods=["GET"])
@jwt_required
@admin_required
def fetch_one_review(recipe_id, rid):
    try:
        recipe_obj_id = ObjectId(recipe_id)
    except InvalidId:
        return make_response(jsonify({"error": "Invalid recipe ID"}), 400)

    # Since review IDs are stored as strings, query by string
    recipe = collection.find_one(
        {"_id": recipe_obj_id, "reviews._id": rid},
        {"_id": 0, "reviews.$": 1}
    )

    if recipe is None or not recipe.get("reviews"):
        return make_response(jsonify({"error": "Review not found"}), 404)

    review = recipe["reviews"][0]
    # Ensure _id is a string
    if not isinstance(review["_id"], str):
        review["_id"] = str(review["_id"])

    return make_response(jsonify(review), 200)

#edit review
@reviews_bp.route("/api/v1.0/recipes/<recipe_id>/reviews/<rid>", methods=["PUT"])
@jwt_required
@admin_required
def edit_review(recipe_id, rid):
    print(f"Recipe ID: {recipe_id}")
    print(f"Review ID: {rid}")
    
    # Get JSON data
    data = request.get_json()
    print(f"Received data: {data}")
    
    if not data:
        return make_response(
            jsonify({"error": "No data provided"}), 400
        )
    
    try:
        stars = int(data.get("stars", ""))
        if stars < 1 or stars > 5:
            return make_response(
                jsonify({"error": "Stars must be between 1 and 5."}), 400
            )
    except (ValueError, TypeError):
        return make_response(
            jsonify({"error": "Stars must be a number between 1 and 5."}), 400
        )
    
    if not data.get("username") or not data.get("comment"):
        return make_response(
            jsonify({"error": "Username and comment are required"}), 400
        )
    
    # Check if review exists - use STRING not ObjectId!
    print(f"Checking if review exists...")
    recipe_with_review = collection.find_one({
        "_id": ObjectId(recipe_id),
        "reviews._id": rid  # ✅ Changed from ObjectId(rid) to rid
    })
    print(f"Recipe with review found: {recipe_with_review is not None}")
    
    if not recipe_with_review:
        print(f"ERROR: Review {rid} not found in recipe {recipe_id}")
        return make_response(
            jsonify({"error": "Review not found in this recipe"}), 404
        )
    
    edited_review = {
        "reviews.$.username": data["username"],
        "reviews.$.comment": data["comment"],
        "reviews.$.stars": stars
    }

    print(f"Attempting to update review...")
    
    result = collection.update_one(
        {
            "_id": ObjectId(recipe_id),
            "reviews._id": rid  # ✅ Changed from ObjectId(rid) to rid
        },
        {"$set": edited_review}
    )
    
    print(f"Matched count: {result.matched_count}")
    print(f"Modified count: {result.modified_count}")

    if result.matched_count == 0:
        return make_response(
            jsonify({"error": "Failed to update review"}), 404
        )

    return make_response(jsonify({
        "message": "Review updated successfully",
        "url": f"http://localhost:5000/api/v1.0/recipes/{recipe_id}/reviews/{rid}"
    }), 200)

#delete review
@reviews_bp.route("/api/v1.0/recipes/<recipe_id>/reviews/<rid>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_review(recipe_id, rid):
    # Query by string since review IDs are stored as strings
    result = collection.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$pull": {"reviews": {"_id": rid}}}  # Changed from ObjectId(rid) to rid
    )

    if result.modified_count == 0:
        return make_response(
            jsonify({"error": "Invalid recipe ID or review ID"}), 404
        )

    return make_response(jsonify({"message": "deleted successfully"}), 200)



#filter review by rating
@reviews_bp.route("/api/v1.0/reviews/filter", methods=["GET"])
def filter_reviews_by_rating():
    stars = request.args.get("stars")
    if not stars or not stars.isdigit():
        return make_response(jsonify({"error": "Invalid or missing stars parameter"}), 400)
    stars = int(stars)

    pipeline = [
        {"$unwind": "$reviews"},
        {"$match": {"reviews.stars": stars}},
        {"$project": {"_id": 0, "recipe_id": {"$toString": "$_id"}, "title": "$Title", "review": "$reviews"}}
    ]

    results = list(collection.aggregate(pipeline))
    for r in results: r["review"]["_id"] = str(r["review"]["_id"])
    return make_response(jsonify(results), 200)