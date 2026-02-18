from flask import Blueprint, jsonify

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return "Dublin Bike Scheme App Running"

@main.route("/api/test")
def test_json():
    return jsonify({
        "status": "success",
        "message": "API is working"
    })
