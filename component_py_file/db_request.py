from component_py_file.db_operations import get_engine
from sqlalchemy import  text
from werkzeug.security import check_password_hash
from datetime import datetime


def request_current_weather():
    """
    Return the latest current weather row as a dict.
    If no data exists, return None.
    """

    engine = get_engine()

    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT
                    time_updated,
                    weather_id,
                    weather_main,
                    weather_description,
                    weather_icon,
                    temp,
                    feels_like,
                    temp_min,
                    temp_max,
                    pressure,
                    humidity,
                    visibility,
                    wind_speed,
                    wind_deg,
                    clouds,
                    sunrise,
                    sunset
                FROM weather_current
                ORDER BY time_updated DESC
                LIMIT 1;
            """)
        ).mappings().first()

    if row is None:
        return None

    return {
        "time_updated": row["time_updated"].isoformat(sep=" ") if row["time_updated"] else None,
        "weather_id": row["weather_id"],
        "weather_main": row["weather_main"],
        "weather_description": row["weather_description"],
        "weather_icon": row["weather_icon"],
        "temp": row["temp"],
        "feels_like": row["feels_like"],
        "temp_min": row["temp_min"],
        "temp_max": row["temp_max"],
        "pressure": row["pressure"],
        "humidity": row["humidity"],
        "visibility": row["visibility"],
        "wind_speed": row["wind_speed"],
        "wind_deg": row["wind_deg"],
        "clouds": row["clouds"],
        "sunrise": row["sunrise"].isoformat(sep=" ") if row["sunrise"] else None,
        "sunset": row["sunset"].isoformat(sep=" ") if row["sunset"] else None,
        "icon_url": f"https://openweathermap.org/img/wn/{row['weather_icon']}@2x.png" if row["weather_icon"] else None,
        "icon_url_big": f"https://openweathermap.org/img/wn/{row['weather_icon']}@4x.png" if row["weather_icon"] else None,
    }


def request_hourly_forecast(limit=16):
    """
    Return hourly forecast rows as a list of dicts, ordered by time_forecast ascending.

    limit:
        how many forecast rows to return
    """

    engine = get_engine()

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT
                    time_forecast,
                    dt_txt,
                    weather_id,
                    weather_main,
                    weather_description,
                    weather_icon,
                    temp,
                    feels_like,
                    temp_min,
                    temp_max,
                    pressure,
                    humidity,
                    visibility,
                    wind_speed,
                    wind_deg,
                    clouds,
                    pop,
                    rain_1h
                FROM weather_forecast_hourly
                WHERE time_forecast >= UTC_TIMESTAMP()
                ORDER BY time_forecast ASC
                LIMIT :limit;
            """),
            {"limit": limit}
        ).mappings().all()

    result = []
    for row in rows:
        result.append({
            "time_forecast": row["time_forecast"].isoformat(sep=" ") if row["time_forecast"] else None,
            "dt_txt": row["dt_txt"].isoformat(sep=" ") if row["dt_txt"] else None,
            "weather_id": row["weather_id"],
            "weather_main": row["weather_main"],
            "weather_description": row["weather_description"],
            "weather_icon": row["weather_icon"],
            "temp": row["temp"],
            "feels_like": row["feels_like"],
            "temp_min": row["temp_min"],
            "temp_max": row["temp_max"],
            "pressure": row["pressure"],
            "humidity": row["humidity"],
            "visibility": row["visibility"],
            "wind_speed": row["wind_speed"],
            "wind_deg": row["wind_deg"],
            "clouds": row["clouds"],
            "prob": row["pop"],
            "rain_1h": row["rain_1h"],
        })

    return result



def request_daily_forecast(limit=7):
    engine = get_engine()

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT
                    time_forecast,
                    sunrise,
                    sunset,
                    temp_morn,
                    temp_day,
                    temp_eve,
                    temp_min,
                    temp_max,
                    feels_like_morn,
                    feels_like_day,
                    feels_like_eve,
                    feels_like_night,
                    pressure,
                    humidity,
                    weather_id,
                    weather_main,
                    weather_description,
                    weather_icon,
                    wind_speed,
                    wind_deg,
                    clouds,
                    pop,
                    rain
                FROM weather_forecast_daily
                WHERE time_forecast >= UTC_TIMESTAMP()
                ORDER BY time_forecast ASC
                LIMIT :limit;
            """),
            {"limit": limit}
        ).mappings().all()

    result = []
    for i, row in enumerate(rows):
        day_label = None
        if row["time_forecast"]:
            day_label = "Today" if i == 0 else row["time_forecast"].strftime("%a")

        result.append({
            "time_forecast": row["time_forecast"].isoformat(sep=" ") if row["time_forecast"] else None,
            "day_label": day_label,
            "sunrise": row["sunrise"].isoformat(sep=" ") if row["sunrise"] else None,
            "sunset": row["sunset"].isoformat(sep=" ") if row["sunset"] else None,
            "temp_morn": row["temp_morn"],
            "temp_day": row["temp_day"],
            "temp_eve": row["temp_eve"],
            "temp_min": row["temp_min"],
            "temp_max": row["temp_max"],
            "feels_like_morn": row["feels_like_morn"],
            "feels_like_day": row["feels_like_day"],
            "feels_like_eve": row["feels_like_eve"],
            "feels_like_night": row["feels_like_night"],
            "pressure": row["pressure"],
            "humidity": row["humidity"],
            "weather_id": row["weather_id"],
            "weather_main": row["weather_main"],
            "weather_description": row["weather_description"],
            "weather_icon": row["weather_icon"],
            "icon_url": f"https://openweathermap.org/img/wn/{row['weather_icon']}@2x.png" if row["weather_icon"] else None,
            "wind_speed": row["wind_speed"],
            "wind_deg": row["wind_deg"],
            "clouds": row["clouds"],
            "rain_probability": row["pop"],
            "rain": row["rain"],
        })

    return result



def request_bike_stations_latest():
    """
    Return latest status for each bike station.
    Output format is compatible with your frontend JS.
    """

    engine = get_engine()

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT
                    bs.station_number AS number,
                    bs.contract_name,
                    bs.name,
                    bs.address,
                    bs.station_lat,
                    bs.station_lon,
                    bs.capacity AS bike_stands,

                    bss.time_updated,
                    bss.status,
                    bss.available_bikes,
                    bss.available_stands AS available_bike_stands

                FROM bike_station bs
                JOIN (
                    SELECT
                        station_number,
                        MAX(time_updated) AS latest_time
                    FROM bike_station_status
                    GROUP BY station_number
                ) latest
                    ON bs.station_number = latest.station_number
                JOIN bike_station_status bss
                    ON bss.station_number = latest.station_number
                   AND bss.time_updated = latest.latest_time

                ORDER BY bs.station_number;
            """)
        ).mappings().all()

    result = []
    for row in rows:
        result.append({
            "number": row["number"],
            "contract_name": row["contract_name"],
            "name": row["name"],
            "address": row["address"],
            "position": {
                "lat": float(row["station_lat"]) if row["station_lat"] is not None else None,
                "lng": float(row["station_lon"]) if row["station_lon"] is not None else None,
            },
            "bike_stands": row["bike_stands"],
            "time_updated": row["time_updated"].isoformat(sep=" ") if row["time_updated"] else None,
            "status": row["status"],
            "available_bikes": row["available_bikes"],
            "available_bike_stands": row["available_bike_stands"],
        })

    return result



def get_user_by_email(email):
    engine = get_engine()

    email = (email or "").strip().lower()
    if not email:
        return None

    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT
                    user_id,
                    email,
                    full_name,
                    password_hash,
                    provider,
                    provider_user_id,
                    is_active,
                    created_at,
                    updated_at,
                    last_login_at
                FROM users
                WHERE email = :email
                LIMIT 1
            """),
            {"email": email}
        ).mappings().fetchone()

        if not row:
            return None

        return dict(row)



def verify_user_login(email, password):
    """
    Returns:
        user dict -> login success
        None      -> login failed
    """
    user = get_user_by_email(email)

    if not user:
        return None

    if not user.get("is_active"):
        return None

    password_hash = user.get("password_hash")
    if not password_hash:
        return None

    if not check_password_hash(password_hash, password):
        return None

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE users
                SET last_login_at = NOW()
                WHERE user_id = :user_id
            """),
            {"user_id": user["user_id"]}
        )

    return user



def add_favourite(user_id, station_number):
    engine = get_engine()

    try:
        user_id = int(user_id)
        station_number = int(station_number)
    except (TypeError, ValueError):
        return False

    with engine.begin() as conn:
        existing = conn.execute(
            text("""
                SELECT favourite_id
                FROM favourites
                WHERE user_id = :user_id
                  AND station_number = :station_number
                LIMIT 1
            """),
            {
                "user_id": user_id,
                "station_number": station_number
            }
        ).fetchone()

        if existing:
            return False

        conn.execute(
            text("""
                INSERT INTO favourites (user_id, station_number)
                VALUES (:user_id, :station_number)
            """),
            {
                "user_id": user_id,
                "station_number": station_number
            }
        )

    return True


def remove_favourite(user_id, station_number):
    engine = get_engine()

    try:
        user_id = int(user_id)
        station_number = int(station_number)
    except (TypeError, ValueError):
        return False

    with engine.begin() as conn:
        result = conn.execute(
            text("""
                DELETE FROM favourites
                WHERE user_id = :user_id
                  AND station_number = :station_number
            """),
            {
                "user_id": user_id,
                "station_number": station_number
            }
        )

    return result.rowcount > 0


def get_user_favourites(user_id):
    engine = get_engine()

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return []

    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT
                    f.favourite_id,
                    f.created_at,
                    bs.station_number,
                    bs.name,
                    bs.address,
                    bs.station_lat,
                    bs.station_lon,
                    bs.capacity,
                    bss.status,
                    bss.available_bikes,
                    bss.available_stands,
                    bss.time_updated
                FROM favourites f
                INNER JOIN bike_station bs
                    ON f.station_number = bs.station_number
                LEFT JOIN bike_station_status bss
                    ON bss.station_number = bs.station_number
                   AND bss.time_updated = (
                        SELECT MAX(bss2.time_updated)
                        FROM bike_station_status bss2
                        WHERE bss2.station_number = bs.station_number
                   )
                WHERE f.user_id = :user_id
                ORDER BY f.created_at DESC
            """),
            {"user_id": user_id}
        ).mappings().all()

    result = []
    for row in rows:
        result.append({
            "favourite_id": row["favourite_id"],
            "number": row["station_number"],
            "name": row["name"],
            "address": row["address"],
            "position": {
                "lat": float(row["station_lat"]) if row["station_lat"] is not None else None,
                "lng": float(row["station_lon"]) if row["station_lon"] is not None else None,
            },
            "bike_stands": row["capacity"],
            "status": row["status"],
            "available_bikes": row["available_bikes"],
            "available_bike_stands": row["available_stands"],
            "time_updated": row["time_updated"].isoformat(sep=" ") if row["time_updated"] else None,
        })

    return result