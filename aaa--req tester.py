import requests

r = requests.get("https://api.openweathermap.org")
print(r.status_code)