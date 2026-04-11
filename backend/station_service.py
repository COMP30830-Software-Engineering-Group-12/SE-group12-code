from math import sqrt
from data_scraping import fetch_bike_data


def distance(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    return sqrt((a_lat - b_lat) ** 2 + (a_lng - b_lng) ** 2)


def fetch_live_stations() -> list:
    """
    Fetch all bike stations from the live API and format them.
    """
    raw = fetch_bike_data()

    if not raw:
        return []

    stations = []

    for s in raw:
        stations.append({
            "station_id": s["number"],
            "name": s["name"],
            "lat": s["position"]["lat"],
            "lng": s["position"]["lng"],
            "bikes_available": s["available_bikes"],
            "docks_available": s["available_bike_stands"],
            "status": s.get("status", "UNKNOWN"),
        })

    return stations


def get_nearest_stations(user_lat: float, user_lng: float, limit: int = 3) -> list:
    """
    Return the closest bike stations to the user's location.
    """
    stations = fetch_live_stations()

    if not stations:
        return []

    ranked = sorted(
        stations,
        key=lambda station: distance(
            user_lat,
            user_lng,
            station["lat"],
            station["lng"]
        )
    )

    return ranked[:limit]
