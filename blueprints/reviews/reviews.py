from flask import Blueprint,request,make_response,jsonify
from bson import ObjectId
from decorators import jwt_required, admin_required

reviews_bp = Blueprint("reviews_bp",__name__)

#review
@reviews_bp.route("/api/v1.0/recipes/<string:id>/reviews", methods=["POST"])
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