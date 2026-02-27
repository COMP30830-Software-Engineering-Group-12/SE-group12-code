from flask import Blueprint, jsonify
from sqlalchemy import text
from .db import get_db

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return "Dublin Bike Scheme App Running"

@main.route("/api/health")
def health():
    return jsonify({"status": "ok"})

@main.route("/api/stations")
def stations():
    engine = get_db()

    rows = engine.execute(text("SELECT * FROM bike_station;")).fetchall()

    # Convert rows to dicts
    stations_list = [dict(row._mapping) for row in rows]

    return jsonify(bike_stations=stations_list)

@main.route("/api/test")
def test_json():
    return jsonify({
        "status": "success",
        "message": "API is working"
    })
