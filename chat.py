from flask import Blueprint, request, jsonify
from chat_service import build_chat_response
from guardrails import validate_message

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    message = data.get("message", "")
    user_lat = data.get("user_lat")
    user_lng = data.get("user_lng")

    validation = validate_message(message)
    if not validation["ok"]:
        return jsonify({
            "reply": validation["reason"],
            "fallback": True
        }), 400

    reply = build_chat_response(
        message=message,
        user_lat=user_lat,
        user_lng=user_lng
    )

    return jsonify({
        "reply": reply,
        "fallback": False
    })