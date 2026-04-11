# appid (api key)
# 4d4258544066d525a65b31c3501fb9cd

import requests

API_KEY = "4d4258544066d525a65b31c3501fb9cd"
r = requests.get(
    "https://api.openweathermap.org/data/2.5/weather",
    params={"q": "Dublin,IE", "appid": API_KEY, "units": "metric"},
    timeout=30
)
print(r.status_code)
print(r.text[:300])