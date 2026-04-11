from station_service import get_nearest_stations
from guardrails import is_bike_related
from prediction_service import predict_bikes_one_hour_ahead


PREDICTION_KEYWORDS = [
    "predict",
    "prediction",
    "forecast",
    "weather",
    "next hour",
    "in an hour",
    "how many bikes will be",
    "how many bikes in an hour",
    "will there be bikes",
]

CURRENT_STATUS_KEYWORDS = [
    "now",
    "current",
    "currently",
    "available",
    "how many bikes are there",
    "nearest station",
    "near me",
]

HELP_KEYWORDS = [
    "help",
    "what can you do",
    "options",
]
def contains_any(message: str, keywords: list[str]) -> bool:
    lower = message.lower()
    return any(term in lower for term in keywords)


def is_prediction_request(message: str) -> bool:
    return contains_any(message, PREDICTION_KEYWORDS)


def is_help_request(message: str) -> bool:
    return contains_any(message, HELP_KEYWORDS)


def build_help_response() -> str:
    return (
        "I can help you find nearby bike stations, check current bike availability, "
        "and estimate how many bikes may be available in the next hour based on live weather conditions. "
        "Try asking something like: 'Where is the nearest bike station?' or "
        "'How many bikes will be there in an hour?'"
    )


def build_location_prompt() -> str:
    return (
        "I can help with that, but I need your location first so I can find the nearest bike station. "
        "Once I have it, I can tell you the current availability or give you a one-hour prediction."
    )


def build_current_station_response(station: dict) -> str:
    bikes = station["bikes_available"]
    docks = station["docks_available"]
    name = station["name"]

    if bikes == 0:
        availability_comment = "There are no bikes available there right now."
    elif bikes <= 3:
        availability_comment = "Bike availability is quite low at the moment."
    else:
        availability_comment = "There seems to be a reasonable number of bikes available."

    return (
        f"The nearest station is {name}. "
        f"It currently has {bikes} bikes available and {docks} empty docks. "
        f"{availability_comment}"
    )


def build_prediction_response(station: dict, forecast: dict) -> str:
    name = station["name"]
    current_bikes = station["bikes_available"]
    predicted_bikes = forecast["predicted_bikes"]
    weather = forecast["weather_summary"]

    if predicted_bikes > current_bikes:
        trend = "Availability is expected to improve slightly."
    elif predicted_bikes < current_bikes:
        trend = "Availability may decrease over the next hour."
    else:
        trend = "Availability is expected to stay about the same."

    return (
        f"The nearest station is {name}. "
        f"It currently has {current_bikes} bikes available. "
        f"Based on the latest weather conditions, I predict there will be about "
        f"{predicted_bikes} bikes available in one hour. "
        f"The expected weather is {weather}. "
        f"{trend}"
    )


def build_general_bike_response(station: dict) -> str:
    return (
        f"I found the nearest station for you: {station['name']}. "
        f"It currently has {station['bikes_available']} bikes available and "
        f"{station['docks_available']} empty docks. "
        f"If you want, you can also ask me for a one-hour bike prediction."
    )


def build_chat_response(message: str, user_lat: float | None = None, user_lng: float | None = None) -> str:
    if is_help_request(message):
        return build_help_response()

    if not is_bike_related(message):
        return (
            "I can help with bike stations, bike availability, short-term bike predictions, "
            "and commuting questions in this app."
        )

    if user_lat is None or user_lng is None:
        return build_location_prompt()

    nearest = get_nearest_stations(user_lat, user_lng)

    if not nearest:
        return (
            "I couldn't find any nearby bike stations right now. "
            "Please try again in a moment."
        )

    top = nearest[0]

    if is_prediction_request(message):
        forecast = predict_bikes_one_hour_ahead(top)

        if forecast is None:
            return (
                f"I found the nearest station, which is {top['name']}, "
                "but I couldn't get the weather data needed to make a prediction right now."
            )

        return build_prediction_response(top, forecast)

    if contains_any(message, CURRENT_STATUS_KEYWORDS):
        return build_current_station_response(top)

    return build_general_bike_response(top)