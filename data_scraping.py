import requests
import dbinfo
import json
import logging


def fetch_bike_data():
    try:
        response = requests.get(
            dbinfo.bike_url,
            params={
                "apiKey": dbinfo.bike_api_key,
                "contract": dbinfo.contract_city
            },
            timeout=10
        )
        response.raise_for_status()
        bike_data = response.json()
        return bike_data

    except Exception as e:
        logging.error("fetch_bike_data failed: %s", e)
    return None


def fetch_bike_data_by_station(station_number):
    try:
        station_url = f"{dbinfo.bike_url}/{station_number}"
        response = requests.get(
            station_url,
            params={
                "apiKey": dbinfo.bike_api_key,
                "contract": dbinfo.contract_city
            },
            timeout=10
        )
        response.raise_for_status()
        station_data = response.json()
        return station_data

    except Exception as e:
        logging.error("fetch_bike_data_by_station failed: %s", e)
    return None


def fetch_weather_forecast_data_hourly():
    try:
        response = requests.get(
            dbinfo.weather_url_forecast_hourly,
            params={
                "appid": dbinfo.weather_api_key,
                "q": dbinfo.q_city,
                "units": "metric",
                "lang": "en",
                "mode": "json"
            },
            timeout=10
        )
        response.raise_for_status()
        weather_data = response.json()
        return weather_data

    except Exception as e:
        logging.error("fetch_weather_forecast_data_hourly failed: %s", e)
    return None


def fetch_weather_forecast_data_daily():
    try:
        response = requests.get(
            dbinfo.weather_url_forecast_daily,
            params={
                "appid": dbinfo.weather_api_key,
                "q": dbinfo.q_city,
                "units": "metric",
                "lang": "en",
                "mode": "json"
            },
            timeout=10
        )
        response.raise_for_status()
        weather_data = response.json()
        return weather_data

    except Exception as e:
        logging.error("fetch_weather_forecast_data_daily failed: %s", e)
    return None


def fetch_weather_current_data():
    try:
        response = requests.get(
            dbinfo.weather_url_current,
            params={
                "appid": dbinfo.weather_api_key,
                "q": dbinfo.q_city,
                "units": "metric",
                "lang": "en",
                "mode": "json"
            },
            timeout=10
        )
        response.raise_for_status()
        weather_data = response.json()
        return weather_data

    except Exception as e:
        logging.error("fetch_weather_current_data failed: %s", e)
    return None


if __name__ == "__main__":
    updated_weather_current_data = fetch_weather_current_data()
    with open("weather_current_data.txt", "w", encoding="utf-8") as f:
        json.dump(updated_weather_current_data, f, indent=4, ensure_ascii=False)

    updated_weather_forecast_data_hourly = fetch_weather_forecast_data_hourly()
    with open("weather_forecast_data_hourly.txt", "w", encoding="utf-8") as f:
        json.dump(updated_weather_forecast_data_hourly, f, indent=4, ensure_ascii=False)

    updated_weather_forecast_data_daily = fetch_weather_forecast_data_daily()
    with open("weather_forecast_data_daily.txt", "w", encoding="utf-8") as f:
        json.dump(updated_weather_forecast_data_daily, f, indent=4, ensure_ascii=False)

    updated_bike_data = fetch_bike_data()
    with open("bike_data.txt", "w", encoding="utf-8") as f:
        json.dump(updated_bike_data, f, indent=4, ensure_ascii=False)

    updated_station_data = fetch_bike_data_by_station(30)
    with open("station_data.txt", "w", encoding="utf-8") as f:
        json.dump(updated_station_data, f, indent=4, ensure_ascii=False)