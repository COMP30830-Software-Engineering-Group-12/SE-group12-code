from typing import Any
from google import genai
from component_py_file import dbinfo

# 你现有函数
from component_py_file.prediction import prediction_by_id
from component_py_file.db_request import (
    request_hourly_forecast, 
    request_bike_stations_latest, 
    get_nearest_stations, 
    get_user_favourites, 
    get_station_by_id, 
    )

# from component_py_file.route_service import plan_route_summary

def get_station_latest_by_id(station_id: int) -> dict | None:
    stations = request_bike_stations_latest()

    for station in stations:
        if int(station["number"]) == int(station_id):
            return station

    return None

client = genai.Client(api_key= dbinfo.GEMINI_API_KEY)


SYSTEM_PROMPT = """
You are the Dublin Bikes assistant inside a bike-sharing web app.

Your job:
- help users check bike station availability
- help users understand weather conditions relevant to cycling
- help users see short-term bike predictions
- help users with favourites and route planning when those tools are available

Rules:
- Never make up station data, weather, or predictions.
- Always rely on tool results.
- If the user asks about "this station", use the selected station if available.
- When a selected station exists, refer to it by station name, not only by station number.
- If the user asks for nearest station but no location is available, ask for location.
- Keep answers concise and helpful.
"""


def tool_get_selected_station_status(station_id: int) -> dict:
    station = get_station_latest_by_id(station_id)

    if not station:
        return {"error": "Station not found"}

    bikes = station.get("available_bikes", 0)
    stands = station.get("available_bike_stands", 0)

    if bikes >= 15:
        availability_status = "High bike availability"
    elif bikes >= 5:
        availability_status = "Moderate bike availability"
    else:
        availability_status = "Low bike availability"

    return {
        "station_id": station["number"],
        "name": station["name"],
        "address": station["address"],
        "lat": station["position"]["lat"],
        "lng": station["position"]["lng"],
        "available_bikes": bikes,
        "available_bike_stands": stands,
        "capacity": station.get("bike_stands"),
        "status": station.get("status"),
        "time_updated": station.get("time_updated"),
        "availability_summary": availability_status,
    }


def tool_get_station_prediction(station_id: int) -> dict[str, Any]:
    result = prediction_by_id(station_id)

    if not result:
        return {"error": "Prediction unavailable"}

    return result


def tool_get_hourly_weather(limit: int = 6) -> dict[str, Any]:
    rows = request_hourly_forecast(limit=limit)

    if not rows:
        return {"error": "Weather forecast unavailable"}

    return {
        "count": len(rows),
        "forecast": rows
    }


def tool_get_nearest_station(user_lat: float, user_lng: float) -> dict[str, Any]:

    stations = get_nearest_stations(user_lat, user_lng)

    if not stations:
        return {"error": "No nearby station found"}

    return stations[0]


def tool_get_user_favourites(user_id: int) -> dict[str, Any]:
 
    favourites = get_user_favourites(user_id)
    return {"favourites": favourites}


def tool_plan_bike_route(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> dict[str, Any]:
    """
    如果你后端已经有 route planner 函数，就接进来。
    """
    try:
        from component_py_file.db_operations import plan_route_summary
    except ImportError:
        return {"error": "Route planner tool is not implemented yet"}

    result = plan_route_summary(from_lat, from_lng, to_lat, to_lng)
    return result


TOOLS = [
    tool_get_selected_station_status,
    tool_get_station_prediction,
    tool_get_hourly_weather,
    tool_get_nearest_station,
    tool_get_user_favourites,
    tool_plan_bike_route,
]

def _build_selected_station_context(selected_station_id: int | None) -> str:
    if selected_station_id is None:
        return "- selected_station: None"

    station = get_station_latest_by_id(selected_station_id)
    if not station:
        return f"- selected_station: id={selected_station_id}, but station not found"

    return (
        f"- selected_station_id: {station['number']}\n"
        f"- selected_station_name: {station['name']}\n"
        f"- selected_station_address: {station['address']}\n"
        f"- selected_station_available_bikes: {station.get('available_bikes')}\n"
        f"- selected_station_available_bike_stands: {station.get('available_bike_stands')}\n"
        f"- selected_station_status: {station.get('status')}"
    )

def _build_context_message(
    message: str,
    user_id: int | None = None,
    user_lat: float | None = None,
    user_lng: float | None = None,
    selected_station_id: int | None = None,
) -> str:
    selected_station_context = _build_selected_station_context(selected_station_id)

    return f"""
User message:
{message}

Context:
- logged_in_user_id: {user_id}
- user_lat: {user_lat}
- user_lng: {user_lng}
{selected_station_context}

Important:
- If the user refers to "this station", prefer the selected station in context.
- When mentioning the selected station, use its name, not only its id.
- If the user asks about nearby stations, use user_lat and user_lng.
- If missing required info, ask a short follow-up question.
""".strip()


def run_gemini_chat(
    message: str,
    user_id: int | None = None,
    user_lat: float | None = None,
    user_lng: float | None = None,
    selected_station_id: int | None = None,
) -> str:
    """
    First version:
    - Gemini can auto-call your Python tools through the SDK.
    - Much simpler than manually parsing tool calls.
    """
    context_message = _build_context_message(
        message=message,
        user_id=user_id,
        user_lat=user_lat,
        user_lng=user_lng,
        selected_station_id=selected_station_id,
    )

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=context_message,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "tools": TOOLS,
        },
    )

    return response.text or "Sorry, I could not generate a reply."