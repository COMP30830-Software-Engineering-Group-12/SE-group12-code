from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from component_py_file import dbinfo
from werkzeug.security import generate_password_hash
from component_py_file.db_operations import create_user
from component_py_file.prediction import prediction_by_id
from component_py_file.gemini_chat import run_gemini_chat
from component_py_file.db_request import (
    request_current_weather,
    request_hourly_forecast,
    request_daily_forecast,
    request_bike_stations_latest,
    verify_user_login,
    add_favourite,
    remove_favourite,
    get_user_favourites
)

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

@app.route("/")
def home():
    current_weather = request_current_weather()
    hourly_forecast = request_hourly_forecast()
    daily_forecast = request_daily_forecast()
    bike_stations_status = request_bike_stations_latest()

    return render_template(
        "index.html",
        current_weather=current_weather,
        hourly_forecast=hourly_forecast,
        daily_forecast=daily_forecast,
        bike_stations_status=bike_stations_status,
        )

@app.route("/map")
def map_page():
    current_weather = request_current_weather()
    bike_stations_status = request_bike_stations_latest()
    return render_template(
        "map.html",
        google_maps_api_key=dbinfo.map_api_key,
        google_maps_map_id=dbinfo.map_id,
        current_weather=current_weather,
        bike_stations_status=bike_stations_status,
    )

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html")

        user = verify_user_login(email, password)

        if not user:
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        session["user_id"] = user["user_id"]
        session["user_email"] = user["email"]
        session["user_full_name"] = user["full_name"]

        return redirect(url_for("home"))

    return render_template("login.html")

@app.route("/logout")
def logout_page():
    session.clear()
    return redirect(url_for("home"))

@app.route("/favourite")
def favourite_page():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return render_template("favourites.html")

@app.route("/signup", methods=["GET", "POST"])
def signup_page():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # 1. basic validation
        if not full_name or not email or not password or not confirm_password:
            flash("Please fill in all fields.", "error")
            return render_template("signup.html")

        # 2. password match
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        # 3. password hashing
        password_hash = generate_password_hash(password)

        # 4. create user in database
        success = create_user(
            email=email,
            full_name=full_name,
            password_hash=password_hash
        )

        if not success:
            flash("This email is already registered.", "error")
            return render_template("signup.html")

        return redirect(url_for("signup_success_page"))

    return render_template("signup.html")

@app.route("/signup-success")
def signup_success_page():
    return render_template("signup_success.html")

@app.route("/weather")
def weather_page():
    return render_template(
        "weather.html",
        current_weather=request_current_weather(),
        hourly_forecast=request_hourly_forecast(),
        daily_forecast=request_daily_forecast(),
    )

@app.route("/api/favourites", methods=["GET"])
def api_get_favourites():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    favourites = get_user_favourites(user_id)
    return jsonify({"success": True, "favourites": favourites})


@app.route("/api/favourites/add", methods=["POST"])
def api_add_favourite():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    station_number = data.get("station_number")

    if station_number is None:
        return jsonify({"success": False, "message": "station_number is required"}), 400

    success = add_favourite(user_id, station_number)

    if not success:
        return jsonify({"success": False, "message": "Could not add favourite"}), 400

    return jsonify({"success": True})


@app.route("/api/favourites/remove", methods=["POST"])
def api_remove_favourite():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    station_number = data.get("station_number")

    if station_number is None:
        return jsonify({"success": False, "message": "station_number is required"}), 400

    success = remove_favourite(user_id, station_number)

    if not success:
        return jsonify({"success": False, "message": "Could not remove favourite"}), 400

    return jsonify({"success": True})

@app.route("/api/current_weather")
def api_current_weather():
    return jsonify(request_current_weather())

@app.route("/api/bike_stations_latest")
def api_bike_stations_latest():
    return jsonify(request_bike_stations_latest())

@app.route("/api/hourly_forecast")
def api_hourly_forecast():
    return jsonify(request_hourly_forecast())

@app.route("/api/daily_forecast")
def api_daily_forecast():
    return jsonify(request_daily_forecast())

@app.route("/api/prediction")
def api_prediction():
    station_id = request.args.get("station_id", type=int)

    if not station_id:
        return jsonify({"error": "station_id required"}), 400

    result = prediction_by_id(station_id)
    return jsonify(result)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}

    message = (data.get("message") or "").strip()
    user_lat = data.get("user_lat")
    user_lng = data.get("user_lng")
    selected_station_id = data.get("selected_station_id")
    user_id = session.get("user_id")

    if not message:
        return jsonify({
            "reply": "Please enter a message."
        }), 400

    try:
        reply = run_gemini_chat(
            message=message,
            user_id=user_id,
            user_lat=user_lat,
            user_lng=user_lng,
            selected_station_id=selected_station_id,
        )

        return jsonify({
            "reply": reply
        })
    except Exception as e:
        print("Chat API error:", e)
        return jsonify({
            "reply": "Sorry, something went wrong while processing your request."
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)