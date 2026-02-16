#This file will focusing on data scraping and formating

import requests
import dbinfo
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

#updated_bike_data = fetch_bike_data()
#print(updated_bike_data)

def fetch_weather_forecast_data():
    try:
        #request data
        response = requests.get(dbinfo.weather_url_forecast, params={"appid": dbinfo.weather_api_key, "q": dbinfo.q_city, "lang": "en", "mode": "json"}, timeout=10)
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
        response = requests.get(dbinfo.weather_url_current, params={"appid": dbinfo.weather_api_key, "q": dbinfo.q_city, "lang": "en", "mode": "json"}, timeout=10)
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
    
updated_weather_current_data = fetch_weather_current_data()
with open("weather_current_data.txt", "w", encoding="utf-8") as f:
    json.dump(updated_weather_current_data, f, indent=4, ensure_ascii=False)

updated_weather_forecast_data = fetch_weather_forecast_data()
with open("weather_forecast_data.txt", "w", encoding="utf-8") as f:
    json.dump(updated_weather_forecast_data, f, indent=4, ensure_ascii=False)

#updated_weather_current_data = fetch_weather_current_data()
#print(updated_weather_current_data, type(updated_weather_current_data))
