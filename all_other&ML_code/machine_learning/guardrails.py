BLOCKED_TOPICS = [
    "medical",
    "diagnosis",
    "investment",
    "crypto",
    "legal advice",
    "weapon",
    "bomb",
    "hack",
    "jailbreak",
]

BIKE_KEYWORDS = [
    "bike",
    "bicycle",
    "station",
    "dock",
    "commute",
    "cycling",
    "route",
    "pickup",
    "drop-off",
    "drop off",
    "availability",
    "near me",
    "destination",
    "city bike",
    "weather",
    "forecast",
    "predict",
    "prediction",
    "next hour",
    "in an hour",
    "nearest",
]


def validate_message(message: str) -> dict:
    if not message or not isinstance(message, str):
        return {"ok": False, "reason": "Message is required."}

    trimmed = message.strip()

    if len(trimmed) == 0:
        return {"ok": False, "reason": "Message cannot be empty."}

    if len(trimmed) > 500:
        return {"ok": False, "reason": "Message is too long."}

    lower = trimmed.lower()

    if any(term in lower for term in BLOCKED_TOPICS):
        return {
            "ok": False,
            "reason": "I can only help with bike stations, routes, and commuting in this app."
        }

    return {"ok": True}


def is_bike_related(message: str) -> bool:
    lower = message.lower()
    return any(term in lower for term in BIKE_KEYWORDS)
