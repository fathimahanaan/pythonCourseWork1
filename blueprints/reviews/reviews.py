from flask import Blueprint,request,make_response,jsonify
from bson import ObjectId
from bson.errors import InvalidId
from decorators import jwt_required, admin_required
import globals

reviews_bp = Blueprint("reviews_bp",__name__)

collection = globals.db.recipes
 
#review
@reviews_bp.route("/api/v1.0/recipes/<string:id>/reviews", methods=["POST"])
@jwt_required
def add_new_review(id):
    try:
        stars = int(request.form.get("stars", "").strip())
        if stars < 1 or stars > 5:
            return make_response(jsonify({"error": "Stars must be between 1 and 5."}), 400)
    except ValueError:
        return make_response(jsonify({"error": "Stars must be a number between 1 and 5."}), 400)
 
    new_review = {
        "_id": ObjectId(),
        "username": request.form["username"],
        "comment": request.form["comment"],
        "stars": int(request.form["stars"])
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
    
             
 
@reviews_bp.route("/api/v1.0/recipes/<string:id>/reviews", methods=["GET"])
def fetch_all_reviews(id):
    data_to_return = []

    # ✅ Validate ObjectId first
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        return make_response(jsonify({"error": "Invalid recipeID"}), 404)

    # ✅ Use the validated obj_id here
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

@reviews_bp.route("/api/v1.0/recipes/<recipe_id>/reviews/<rid>", methods=["GET"])
@jwt_required
def fetch_one_review(recipe_id, rid):
    recipe = collection.find_one(
        {"reviews._id": ObjectId(rid)},
        {"_id": 0, "reviews.$": 1}
    )

    if recipe is None:
        return make_response(
            jsonify({"error": "Invalid business ID or review ID"}), 404
        )

    recipe["reviews"][0]["_id"] = str(recipe["reviews"][0]["_id"])

    return make_response(jsonify(recipe["reviews"][0]), 200)



@reviews_bp.route("/api/v1.0/recipes/<recipe_id>/reviews/<rid>", methods=["PUT"])
@jwt_required
@admin_required
def edit_review(recipe_id, rid):
    try:
        stars = int(request.form.get("stars", "").strip())
        if stars < 1 or stars > 5:
            return  make_response(
            jsonify({"error": "Stars must be between 1 and 5."}), 400)
    except ValueError:
        return  make_response(
            jsonify({"error": "Stars must be a number between 1 and 5."}), 400)
    
    edited_review = {
        "reviews.$.username": request.form["username"],
        "reviews.$.comment": request.form["comment"],
        "reviews.$.stars": request.form["stars"]
    }

    result = collection.update_one(
        {"reviews._id": ObjectId(rid)},
        {"$set": edited_review}
    )

    if result.matched_count == 0:
        return make_response(
            jsonify({"error": "Invalid recipe ID or review ID"}), 404
        )

    edit_review_url = (
        f"http://localhost:5000/api/v1.0/recipes/{recipe_id}/reviews/{rid}"
    )

    return make_response(jsonify({"url": edit_review_url}), 200)


@reviews_bp.route("/api/v1.0/recipes/<recipe_id>/reviews/<rid>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_review(recipe_id, rid):
    result = collection.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$pull": {"reviews": {"_id": ObjectId(rid)}}}
    )

    if result.modified_count == 0:
        return make_response(
            jsonify({"error": "Invalid recipe ID or review ID"}), 404
        )

    return make_response(jsonify({"message":"deleted successfully"}), 204)



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