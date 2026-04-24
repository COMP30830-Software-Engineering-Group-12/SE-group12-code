
#set parameter for bike data requests
bike_api_key = "Hidden"
bike_url = "https://api.jcdecaux.com/vls/v1/stations"
contract_city = "dublin"

#set parameter for weather data requests
weather_api_key = "Hidden"
weather_url_forecast_hourly = "https://api.openweathermap.org/data/2.5/forecast"
weather_url_forecast_daily = "https://api.openweathermap.org/data/2.5/forecast/daily"
weather_url_current = "https://api.openweathermap.org/data/2.5/weather"
q_city = "Dublin,IE"


#set parameter for sql connection
sqlusername = "" #fill with your own sql info
sqlpassword = "" #fill with your own sql info
sqlport = "3306"
sqlurl = "127.0.0.1"

#database & table name
db_name = "bike_system"
#bike_table = "bike_data"
weather_current_table = "weather_current"
weather_forecast_table = "weather_forecast"
