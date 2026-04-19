#This file will focusing on data scraping

import requests
from component_py_file import dbinfo
import json

def fetch_bike_data():
    try:
        #request data
        response = requests.get(dbinfo.bike_url, params={"apiKey": dbinfo.bike_api_key, "contract": dbinfo.contract_city}, timeout=10)
        #check response status
        response.raise_for_status()
        #save data
        bike_data = response.json()

        print("Request successful!")
        return bike_data

    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred:", e)
    except requests.exceptions.ConnectionError:
        print("Network connection error")
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.RequestException as e:
        print("Other request error:", e)
    #if there is any error, return None
    return None

def fetch_bike_data_by_station(station_number):
    try:
        #request data
        station_url = f"{dbinfo.bike_url}/{station_number}"
        response = requests.get(station_url, params={"apiKey": dbinfo.bike_api_key, "contract": dbinfo.contract_city}, timeout=10)
        #check response status
        response.raise_for_status()
        #save data
        station_data = response.json()

        print("Request successful!")
        return station_data

    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred:", e)
    except requests.exceptions.ConnectionError:
        print("Network connection error")
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.RequestException as e:
        print("Other request error:", e)
    #if there is any error, return None
    return None


def fetch_weather_forecast_data_hourly():
    try:
        #request data
        response = requests.get(dbinfo.weather_url_forecast_hourly, params={"appid": dbinfo.weather_api_key, "q": dbinfo.q_city, "units": "metric", "lang": "en", "mode": "json"}, timeout=10)
        #check response status
        response.raise_for_status()
        #save data
        weather_data = response.json()

        print("Request successful!")
        return weather_data

    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred:", e)
    except requests.exceptions.ConnectionError:
        print("Network connection error")
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.RequestException as e:
        print("Other request error:", e)
    #if there is any error, return None
    return None

def fetch_weather_forecast_data_daily():
    try:
        #request data
        response = requests.get(dbinfo.weather_url_forecast_daily, params={"appid": dbinfo.weather_api_key, "q": dbinfo.q_city, "units": "metric", "lang": "en", "mode": "json"}, timeout=10)
        #check response status
        response.raise_for_status()
        #save data
        weather_data = response.json()

        print("Request successful!")
        return weather_data

    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred:", e)
    except requests.exceptions.ConnectionError:
        print("Network connection error")
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.RequestException as e:
        print("Other request error:", e)
    #if there is any error, return None
    return None

def fetch_weather_current_data():
    try:
        #request data
        response = requests.get(dbinfo.weather_url_current, params={"appid": dbinfo.weather_api_key, "q": dbinfo.q_city, "units": "metric", "lang": "en", "mode": "json"}, timeout=10)
        #check response status
        response.raise_for_status()
        #save data
        weather_data = response.json()

        print("Request successful!")
        return weather_data

    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred:", e)
    except requests.exceptions.ConnectionError:
        print("Network connection error")
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.RequestException as e:
        print("Other request error:", e)
    #if there is any error, return None
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