import sys
import types
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from werkzeug.security import generate_password_hash


# ---------------------------------------------------------
# Optional stub for google.genai
# This prevents tests from calling real Gemini API.
# ---------------------------------------------------------
if "google" not in sys.modules:
    google_module = types.ModuleType("google")
    genai_module = types.ModuleType("google.genai")

    class FakeGenAIClient:
        def __init__(self, *args, **kwargs):
            self.models = MagicMock()

    genai_module.Client = FakeGenAIClient
    google_module.genai = genai_module

    sys.modules["google"] = google_module
    sys.modules["google.genai"] = genai_module


# ---------------------------------------------------------
# Imports from your project
# ---------------------------------------------------------
from component_py_file import data_scraping
from component_py_file import db_request
from component_py_file import prediction
from component_py_file import gemini_chat
import app_flask


# ---------------------------------------------------------
# Fake database helpers
# ---------------------------------------------------------
class FakeExecuteResult:
    def __init__(self, first=None, all_rows=None, fetchone=None, rowcount=1):
        self._first = first
        self._all_rows = all_rows or []
        self._fetchone = fetchone
        self.rowcount = rowcount

    def mappings(self):
        return self

    def first(self):
        return self._first

    def fetchone(self):
        return self._fetchone

    def all(self):
        return self._all_rows


class FakeConnection:
    def __init__(self, results):
        self.results = list(results)
        self.executed = []

    def execute(self, *args, **kwargs):
        self.executed.append((args, kwargs))
        if self.results:
            return self.results.pop(0)
        return FakeExecuteResult()


class FakeContextManager:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class FakeEngine:
    def __init__(self, results):
        self.conn = FakeConnection(results)

    def connect(self):
        return FakeContextManager(self.conn)

    def begin(self):
        return FakeContextManager(self.conn)


# ---------------------------------------------------------
# data_scraping.py tests
# ---------------------------------------------------------
class TestDataScraping(unittest.TestCase):

    @patch("component_py_file.data_scraping.requests.get")
    def test_fetch_bike_data_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"number": 1, "name": "Station A"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = data_scraping.fetch_bike_data()

        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["name"], "Station A")

    @patch("component_py_file.data_scraping.requests.get")
    def test_fetch_bike_data_by_station_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"number": 30, "name": "Station 30"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = data_scraping.fetch_bike_data_by_station(30)

        self.assertEqual(result["number"], 30)
        self.assertEqual(result["name"], "Station 30")

    @patch("component_py_file.data_scraping.requests.get")
    def test_fetch_weather_hourly_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"list": [{"temp": 15}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = data_scraping.fetch_weather_forecast_data_hourly()

        self.assertIn("list", result)

    @patch("component_py_file.data_scraping.requests.get")
    def test_fetch_weather_daily_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"list": [{"temp": {"day": 16}}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = data_scraping.fetch_weather_forecast_data_daily()

        self.assertIn("list", result)

    @patch("component_py_file.data_scraping.requests.get")
    def test_fetch_weather_current_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "weather": [{"main": "Clear"}],
            "main": {"temp": 18}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = data_scraping.fetch_weather_current_data()

        self.assertEqual(result["weather"][0]["main"], "Clear")
        self.assertEqual(result["main"]["temp"], 18)

    @patch("component_py_file.data_scraping.requests.get")
    def test_fetch_api_failure_returns_none(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("API error")

        result = data_scraping.fetch_bike_data()

        self.assertIsNone(result)


# ---------------------------------------------------------
# db_request.py helper function tests
# ---------------------------------------------------------
class TestDBRequestHelpers(unittest.TestCase):

    def test_calculate_cycling_score_excellent(self):
        score = db_request.calculate_cycling_score(
            temp=18,
            weather_main="Clear",
            wind_speed=2
        )
        self.assertEqual(score, 10.0)

    def test_calculate_cycling_score_poor(self):
        score = db_request.calculate_cycling_score(
            temp=2,
            weather_main="Thunderstorm",
            wind_speed=12
        )
        self.assertLess(score, 3)

    def test_calculate_cycling_score_missing_values(self):
        score = db_request.calculate_cycling_score(
            temp=None,
            weather_main="Unknown",
            wind_speed=None
        )
        self.assertEqual(score, 5.0)

    def test_get_score_label(self):
        self.assertEqual(db_request.get_score_label(9), "Excellent")
        self.assertEqual(db_request.get_score_label(7), "Good")
        self.assertEqual(db_request.get_score_label(5), "Moderate")
        self.assertEqual(db_request.get_score_label(3), "Poor")

    def test_haversine_distance(self):
        distance = db_request._haversine_distance_km(
            53.3498, -6.2603,
            53.3500, -6.2600
        )
        self.assertGreaterEqual(distance, 0)


# ---------------------------------------------------------
# db_request.py database read tests
# ---------------------------------------------------------
class TestDBRequestDatabaseFunctions(unittest.TestCase):

    @patch("component_py_file.db_request.get_engine")
    def test_request_current_weather_success(self, mock_get_engine):
        row = {
            "time_updated": datetime(2025, 1, 1, 10, 0),
            "weather_id": 800,
            "weather_main": "Clear",
            "weather_description": "clear sky",
            "weather_icon": "01d",
            "temp": 18,
            "feels_like": 18,
            "temp_min": 16,
            "temp_max": 20,
            "pressure": 1010,
            "humidity": 60,
            "visibility": 10000,
            "wind_speed": 2,
            "wind_deg": 120,
            "clouds": 0,
            "sunrise": datetime(2025, 1, 1, 8, 0),
            "sunset": datetime(2025, 1, 1, 17, 0),
        }

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(first=row)
        ])

        result = db_request.request_current_weather()

        self.assertEqual(result["weather_main"], "Clear")
        self.assertEqual(result["cycling_score"], 10.0)
        self.assertEqual(result["cycling_label"], "Excellent")
        self.assertIn("icon_url", result)

    @patch("component_py_file.db_request.get_engine")
    def test_request_current_weather_no_data(self, mock_get_engine):
        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(first=None)
        ])

        result = db_request.request_current_weather()

        self.assertIsNone(result)

    @patch("component_py_file.db_request.get_engine")
    def test_request_hourly_forecast_success(self, mock_get_engine):
        rows = [
            {
                "time_forecast": datetime(2025, 1, 1, 10, 0),
                "dt_txt": datetime(2025, 1, 1, 10, 0),
                "weather_id": 800,
                "weather_main": "Clear",
                "weather_description": "clear sky",
                "weather_icon": "01d",
                "temp": 18,
                "feels_like": 18,
                "temp_min": 16,
                "temp_max": 20,
                "pressure": 1010,
                "humidity": 60,
                "visibility": 10000,
                "wind_speed": 2,
                "wind_deg": 120,
                "clouds": 0,
                "pop": 0.1,
                "rain_1h": 0,
            }
        ]

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(all_rows=rows)
        ])

        result = db_request.request_hourly_forecast(limit=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["weather_main"], "Clear")
        self.assertEqual(result[0]["prob"], 0.1)

    @patch("component_py_file.db_request.get_engine")
    def test_request_daily_forecast_success(self, mock_get_engine):
        rows = [
            {
                "time_forecast": datetime(2025, 1, 1),
                "sunrise": datetime(2025, 1, 1, 8, 0),
                "sunset": datetime(2025, 1, 1, 17, 0),
                "temp_morn": 10,
                "temp_day": 15,
                "temp_eve": 12,
                "temp_min": 8,
                "temp_max": 16,
                "feels_like_morn": 9,
                "feels_like_day": 15,
                "feels_like_eve": 11,
                "feels_like_night": 7,
                "pressure": 1010,
                "humidity": 60,
                "weather_id": 800,
                "weather_main": "Clear",
                "weather_description": "clear sky",
                "weather_icon": "01d",
                "wind_speed": 2,
                "wind_deg": 120,
                "clouds": 0,
                "pop": 0.2,
                "rain": 0,
            }
        ]

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(all_rows=rows)
        ])

        result = db_request.request_daily_forecast(limit=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["day_label"], "Today")
        self.assertEqual(result[0]["rain_probability"], 0.2)

    @patch("component_py_file.db_request.get_engine")
    def test_request_bike_stations_latest_success(self, mock_get_engine):
        rows = [
            {
                "number": 1,
                "contract_name": "dublin",
                "name": "Station A",
                "address": "Address A",
                "station_lat": 53.1,
                "station_lon": -6.1,
                "bike_stands": 20,
                "time_updated": datetime(2025, 1, 1, 10, 0),
                "status": "OPEN",
                "available_bikes": 7,
                "available_bike_stands": 13,
            }
        ]

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(all_rows=rows)
        ])

        result = db_request.request_bike_stations_latest()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Station A")
        self.assertEqual(result[0]["position"]["lat"], 53.1)

    @patch("component_py_file.db_request.get_engine")
    def test_get_user_by_email_success(self, mock_get_engine):
        row = {
            "user_id": 1,
            "email": "test@example.com",
            "full_name": "Test User",
            "password_hash": "hash",
            "provider": None,
            "provider_user_id": None,
            "is_active": True,
            "created_at": None,
            "updated_at": None,
            "last_login_at": None,
        }

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(fetchone=row)
        ])

        result = db_request.get_user_by_email(" TEST@example.com ")

        self.assertEqual(result["email"], "test@example.com")

    def test_get_user_by_email_empty(self):
        self.assertIsNone(db_request.get_user_by_email(""))

    @patch("component_py_file.db_request.get_engine")
    @patch("component_py_file.db_request.get_user_by_email")
    def test_verify_user_login_success(self, mock_get_user, mock_get_engine):
        password_hash = generate_password_hash("password123")
        mock_get_user.return_value = {
            "user_id": 1,
            "email": "test@example.com",
            "full_name": "Test User",
            "password_hash": password_hash,
            "is_active": True,
        }

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult()
        ])

        result = db_request.verify_user_login("test@example.com", "password123")

        self.assertIsNotNone(result)
        self.assertEqual(result["user_id"], 1)

    @patch("component_py_file.db_request.get_user_by_email")
    def test_verify_user_login_wrong_password(self, mock_get_user):
        password_hash = generate_password_hash("password123")
        mock_get_user.return_value = {
            "user_id": 1,
            "email": "test@example.com",
            "password_hash": password_hash,
            "is_active": True,
        }

        result = db_request.verify_user_login("test@example.com", "wrong")

        self.assertIsNone(result)

    def test_add_favourite_invalid_input(self):
        result = db_request.add_favourite("abc", 1)
        self.assertFalse(result)

    @patch("component_py_file.db_request.get_engine")
    def test_add_favourite_success(self, mock_get_engine):
        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(fetchone=None),
            FakeExecuteResult()
        ])

        result = db_request.add_favourite(1, 10)

        self.assertTrue(result)

    @patch("component_py_file.db_request.get_engine")
    def test_add_favourite_duplicate(self, mock_get_engine):
        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(fetchone={"favourite_id": 1})
        ])

        result = db_request.add_favourite(1, 10)

        self.assertFalse(result)

    @patch("component_py_file.db_request.get_engine")
    def test_remove_favourite_success(self, mock_get_engine):
        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(rowcount=1)
        ])

        result = db_request.remove_favourite(1, 10)

        self.assertTrue(result)

    def test_remove_favourite_invalid_input(self):
        result = db_request.remove_favourite(None, 10)
        self.assertFalse(result)

    @patch("component_py_file.db_request.get_engine")
    def test_get_user_favourites_success(self, mock_get_engine):
        rows = [
            {
                "favourite_id": 1,
                "created_at": datetime(2025, 1, 1),
                "station_number": 10,
                "name": "Station A",
                "address": "Address A",
                "station_lat": 53.1,
                "station_lon": -6.1,
                "capacity": 20,
                "status": "OPEN",
                "available_bikes": 5,
                "available_stands": 15,
                "time_updated": datetime(2025, 1, 1, 10, 0),
            }
        ]

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(all_rows=rows)
        ])

        result = db_request.get_user_favourites(1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Station A")

    def test_get_user_favourites_invalid_user_id(self):
        result = db_request.get_user_favourites("abc")
        self.assertEqual(result, [])

    @patch("component_py_file.db_request.get_engine")
    def test_get_station_by_id_success(self, mock_get_engine):
        row = {
            "station_number": 1,
            "contract_name": "dublin",
            "name": "Station A",
            "address": "Address A",
            "station_lat": 53.1,
            "station_lon": -6.1,
            "capacity": 20,
        }

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(first=row)
        ])

        result = db_request.get_station_by_id(1)

        self.assertEqual(result["name"], "Station A")

    @patch("component_py_file.db_request.get_engine")
    def test_get_stations_info_success(self, mock_get_engine):
        rows = [
            {
                "station_number": 1,
                "contract_name": "dublin",
                "name": "Station A",
                "address": "Address A",
                "station_lat": 53.1,
                "station_lon": -6.1,
                "capacity": 20,
            }
        ]

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(all_rows=rows)
        ])

        result = db_request.get_stations_info()

        self.assertEqual(result[0]["position"]["lng"], -6.1)

    @patch("component_py_file.db_request.get_stations_info")
    def test_get_nearest_stations_success(self, mock_get_stations):
        mock_get_stations.return_value = [
            {
                "station_number": 1,
                "name": "Near Station",
                "station_lat": 53.3500,
                "station_lon": -6.2600,
            },
            {
                "station_number": 2,
                "name": "Far Station",
                "station_lat": 54.0000,
                "station_lon": -7.0000,
            },
        ]

        result = db_request.get_nearest_stations(53.3498, -6.2603, limit=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Near Station")

    def test_get_nearest_stations_missing_location(self):
        result = db_request.get_nearest_stations(None, -6.2603)
        self.assertEqual(result, [])

    @patch("component_py_file.db_request.get_engine")
    def test_get_or_create_oauth_user_existing(self, mock_get_engine):
        existing = {
            "user_id": 1,
            "email": "test@example.com",
            "full_name": "Test User",
        }

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(first=existing),
            FakeExecuteResult()
        ])

        result = db_request.get_or_create_oauth_user(
            " TEST@example.com ",
            "Test User",
            "google",
            "google123"
        )

        self.assertEqual(result["user_id"], 1)

    @patch("component_py_file.db_request.get_engine")
    def test_get_or_create_oauth_user_new(self, mock_get_engine):
        new_user = {
            "user_id": 2,
            "email": "new@example.com",
            "full_name": "New User",
        }

        mock_get_engine.return_value = FakeEngine([
            FakeExecuteResult(first=None),
            FakeExecuteResult(),
            FakeExecuteResult(first=new_user)
        ])

        result = db_request.get_or_create_oauth_user(
            "new@example.com",
            "New User",
            "google",
            "google456"
        )

        self.assertEqual(result["user_id"], 2)


# ---------------------------------------------------------
# prediction.py tests
# ---------------------------------------------------------
class TestPrediction(unittest.TestCase):

    @patch("component_py_file.prediction.get_prediction_model")
    @patch("component_py_file.prediction.request_hourly_forecast")
    @patch("component_py_file.prediction.get_station_by_id")
    def test_prediction_by_id_success(
        self,
        mock_get_station,
        mock_forecast,
        mock_model
    ):
        mock_get_station.return_value = {
            "station_number": 1,
            "name": "Station A",
            "capacity": 20,
        }

        mock_forecast.return_value = [
            {"time_forecast": "2025-01-01 09:00:00"},
            {
                "time_forecast": "2025-01-01 10:00:00",
                "dt_txt": "2025-01-01 10:00:00",
                "temp": 15,
                "humidity": 70,
                "wind_speed": 3,
                "rain_1h": 0,
            }
        ]

        fake_model = MagicMock()
        fake_model.predict.return_value = [12.4]
        mock_model.return_value = fake_model

        result = prediction.prediction_by_id(1)

        self.assertIsNotNone(result)
        self.assertEqual(result["station"]["name"], "Station A")
        self.assertEqual(result["predictions"][0]["predicted_bikes"], 12)

    @patch("component_py_file.prediction.get_station_by_id")
    def test_prediction_station_not_found(self, mock_get_station):
        mock_get_station.return_value = None

        result = prediction.prediction_by_id(999)

        self.assertIsNone(result)

    @patch("component_py_file.prediction.request_hourly_forecast")
    @patch("component_py_file.prediction.get_station_by_id")
    def test_prediction_no_forecast(self, mock_get_station, mock_forecast):
        mock_get_station.return_value = {
            "station_number": 1,
            "capacity": 20,
        }
        mock_forecast.return_value = []

        result = prediction.prediction_by_id(1)

        self.assertIsNone(result)

    @patch("component_py_file.prediction.get_prediction_model")
    @patch("component_py_file.prediction.request_hourly_forecast")
    @patch("component_py_file.prediction.get_station_by_id")
    def test_prediction_is_capped_by_capacity(
        self,
        mock_get_station,
        mock_forecast,
        mock_model
    ):
        mock_get_station.return_value = {
            "station_number": 1,
            "capacity": 10,
        }

        mock_forecast.return_value = [
            {"time_forecast": "2025-01-01 09:00:00"},
            {
                "time_forecast": "2025-01-01 10:00:00",
                "dt_txt": "2025-01-01 10:00:00",
                "temp": 15,
                "humidity": 70,
                "wind_speed": 3,
                "rain_1h": 0,
            }
        ]

        fake_model = MagicMock()
        fake_model.predict.return_value = [99]
        mock_model.return_value = fake_model

        result = prediction.prediction_by_id(1)

        self.assertEqual(result["predictions"][0]["predicted_bikes"], 10)


# ---------------------------------------------------------
# gemini_chat.py tests
# ---------------------------------------------------------
class TestGeminiChat(unittest.TestCase):

    @patch("component_py_file.gemini_chat.request_bike_stations_latest")
    def test_get_station_latest_by_id_found(self, mock_latest):
        mock_latest.return_value = [
            {"number": 1, "name": "Station A"},
            {"number": 2, "name": "Station B"},
        ]

        result = gemini_chat.get_station_latest_by_id(2)

        self.assertEqual(result["name"], "Station B")

    @patch("component_py_file.gemini_chat.request_bike_stations_latest")
    def test_get_station_latest_by_id_not_found(self, mock_latest):
        mock_latest.return_value = [{"number": 1, "name": "Station A"}]

        result = gemini_chat.get_station_latest_by_id(99)

        self.assertIsNone(result)

    @patch("component_py_file.gemini_chat.get_station_latest_by_id")
    def test_tool_get_selected_station_status_high(self, mock_station):
        mock_station.return_value = {
            "number": 1,
            "name": "Station A",
            "address": "Address A",
            "position": {"lat": 53.1, "lng": -6.1},
            "available_bikes": 16,
            "available_bike_stands": 4,
            "bike_stands": 20,
            "status": "OPEN",
            "time_updated": "2025-01-01 10:00:00",
        }

        result = gemini_chat.tool_get_selected_station_status(1)

        self.assertEqual(result["availability_summary"], "High bike availability")

    @patch("component_py_file.gemini_chat.get_station_latest_by_id")
    def test_tool_get_selected_station_status_not_found(self, mock_station):
        mock_station.return_value = None

        result = gemini_chat.tool_get_selected_station_status(999)

        self.assertIn("error", result)

    @patch("component_py_file.gemini_chat.prediction_by_id")
    def test_tool_get_station_prediction_success(self, mock_prediction):
        mock_prediction.return_value = {
            "station": {"name": "Station A"},
            "predictions": []
        }

        result = gemini_chat.tool_get_station_prediction(1)

        self.assertIn("station", result)

    @patch("component_py_file.gemini_chat.prediction_by_id")
    def test_tool_get_station_prediction_unavailable(self, mock_prediction):
        mock_prediction.return_value = None

        result = gemini_chat.tool_get_station_prediction(999)

        self.assertIn("error", result)

    @patch("component_py_file.gemini_chat.request_hourly_forecast")
    def test_tool_get_hourly_weather_success(self, mock_weather):
        mock_weather.return_value = [{"temp": 15}, {"temp": 16}]

        result = gemini_chat.tool_get_hourly_weather(limit=2)

        self.assertEqual(result["count"], 2)

    @patch("component_py_file.gemini_chat.request_hourly_forecast")
    def test_tool_get_hourly_weather_unavailable(self, mock_weather):
        mock_weather.return_value = []

        result = gemini_chat.tool_get_hourly_weather()

        self.assertIn("error", result)

    @patch("component_py_file.gemini_chat.get_nearest_stations")
    def test_tool_get_nearest_station_success(self, mock_nearest):
        mock_nearest.return_value = [{"name": "Nearest Station"}]

        result = gemini_chat.tool_get_nearest_station(53.1, -6.1)

        self.assertEqual(result["name"], "Nearest Station")

    @patch("component_py_file.gemini_chat.get_nearest_stations")
    def test_tool_get_nearest_station_none(self, mock_nearest):
        mock_nearest.return_value = []

        result = gemini_chat.tool_get_nearest_station(53.1, -6.1)

        self.assertIn("error", result)

    @patch("component_py_file.gemini_chat.get_user_favourites")
    def test_tool_get_user_favourites(self, mock_favourites):
        mock_favourites.return_value = [{"name": "Station A"}]

        result = gemini_chat.tool_get_user_favourites(1)

        self.assertEqual(len(result["favourites"]), 1)

    def test_build_context_message(self):
        text = gemini_chat._build_context_message(
            message="How many bikes?",
            user_id=1,
            user_lat=53.1,
            user_lng=-6.1,
            selected_station_id=None,
        )

        self.assertIn("How many bikes?", text)
        self.assertIn("logged_in_user_id: 1", text)

    @patch("component_py_file.gemini_chat.client")
    def test_run_gemini_chat_success(self, mock_client):
        fake_response = MagicMock()
        fake_response.text = "There are bikes available."
        mock_client.models.generate_content.return_value = fake_response

        result = gemini_chat.run_gemini_chat("Hello")

        self.assertEqual(result, "There are bikes available.")

    @patch("component_py_file.gemini_chat.client")
    def test_run_gemini_chat_empty_response(self, mock_client):
        fake_response = MagicMock()
        fake_response.text = ""
        mock_client.models.generate_content.return_value = fake_response

        result = gemini_chat.run_gemini_chat("Hello")

        self.assertEqual(result, "Sorry, I could not generate a reply.")


# ---------------------------------------------------------
# app_flask.py API route tests
# ---------------------------------------------------------
class TestFlaskAppRoutes(unittest.TestCase):

    def setUp(self):
        app_flask.app.config["TESTING"] = True
        app_flask.app.config["WTF_CSRF_ENABLED"] = False
        self.client = app_flask.app.test_client()

    @patch("app_flask.request_current_weather")
    def test_api_current_weather(self, mock_weather):
        mock_weather.return_value = {"temp": 18, "weather_main": "Clear"}

        response = self.client.get("/api/current_weather")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["temp"], 18)

    @patch("app_flask.request_bike_stations_latest")
    def test_api_bike_stations_latest(self, mock_stations):
        mock_stations.return_value = [
            {"number": 1, "name": "Station A", "available_bikes": 5}
        ]

        response = self.client.get("/api/bike_stations_latest")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]["name"], "Station A")

    @patch("app_flask.request_hourly_forecast")
    def test_api_hourly_forecast(self, mock_hourly):
        mock_hourly.return_value = [{"temp": 15}]

        response = self.client.get("/api/hourly_forecast")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]["temp"], 15)

    @patch("app_flask.request_daily_forecast")
    def test_api_daily_forecast(self, mock_daily):
        mock_daily.return_value = [{"temp_day": 15}]

        response = self.client.get("/api/daily_forecast")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]["temp_day"], 15)

    def test_api_prediction_missing_station_id(self):
        response = self.client.get("/api/prediction")

        self.assertEqual(response.status_code, 400)

    @patch("app_flask.prediction_by_id")
    def test_api_prediction_success(self, mock_prediction):
        mock_prediction.return_value = {
            "station": {"station_number": 1, "name": "Station A"},
            "predictions": [{"predicted_bikes": 12}]
        }

        response = self.client.get("/api/prediction?station_id=1")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["station"]["name"], "Station A")

    def test_api_chat_empty_message(self):
        response = self.client.post("/api/chat", json={"message": ""})
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["reply"], "Please enter a message.")

    @patch("app_flask.run_gemini_chat")
    def test_api_chat_success(self, mock_chat):
        mock_chat.return_value = "Hello from Gemini"

        response = self.client.post("/api/chat", json={"message": "hello"})
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["reply"], "Hello from Gemini")

    @patch("app_flask.run_gemini_chat")
    def test_api_chat_error(self, mock_chat):
        mock_chat.side_effect = Exception("Gemini error")

        response = self.client.post("/api/chat", json={"message": "hello"})
        data = response.get_json()

        self.assertEqual(response.status_code, 500)
        self.assertIn("Sorry", data["reply"])

    def test_api_get_favourites_not_logged_in(self):
        response = self.client.get("/api/favourites")

        self.assertEqual(response.status_code, 401)

    @patch("app_flask.get_user_favourites")
    def test_api_get_favourites_logged_in(self, mock_favourites):
        mock_favourites.return_value = [{"name": "Station A"}]

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        response = self.client.get("/api/favourites")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["favourites"][0]["name"], "Station A")

    def test_api_add_favourite_not_logged_in(self):
        response = self.client.post(
            "/api/favourites/add",
            json={"station_number": 1}
        )

        self.assertEqual(response.status_code, 401)

    def test_api_add_favourite_missing_station_number(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        response = self.client.post("/api/favourites/add", json={})

        self.assertEqual(response.status_code, 400)

    @patch("app_flask.add_favourite")
    def test_api_add_favourite_success(self, mock_add):
        mock_add.return_value = True

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        response = self.client.post(
            "/api/favourites/add",
            json={"station_number": 10}
        )
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])

    @patch("app_flask.add_favourite")
    def test_api_add_favourite_failure(self, mock_add):
        mock_add.return_value = False

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        response = self.client.post(
            "/api/favourites/add",
            json={"station_number": 10}
        )

        self.assertEqual(response.status_code, 400)

    def test_api_remove_favourite_not_logged_in(self):
        response = self.client.post(
            "/api/favourites/remove",
            json={"station_number": 1}
        )

        self.assertEqual(response.status_code, 401)

    def test_api_remove_favourite_missing_station_number(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        response = self.client.post("/api/favourites/remove", json={})

        self.assertEqual(response.status_code, 400)

    @patch("app_flask.remove_favourite")
    def test_api_remove_favourite_success(self, mock_remove):
        mock_remove.return_value = True

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        response = self.client.post(
            "/api/favourites/remove",
            json={"station_number": 10}
        )
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])

    @patch("app_flask.remove_favourite")
    def test_api_remove_favourite_failure(self, mock_remove):
        mock_remove.return_value = False

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        response = self.client.post(
            "/api/favourites/remove",
            json={"station_number": 10}
        )

        self.assertEqual(response.status_code, 400)

    @patch("app_flask.render_template")
    @patch("app_flask.request_current_weather")
    @patch("app_flask.request_hourly_forecast")
    @patch("app_flask.request_daily_forecast")
    @patch("app_flask.request_bike_stations_latest")
    def test_home_page(
        self,
        mock_stations,
        mock_daily,
        mock_hourly,
        mock_weather,
        mock_render
    ):
        mock_weather.return_value = {}
        mock_hourly.return_value = []
        mock_daily.return_value = []
        mock_stations.return_value = []
        mock_render.return_value = "home page"

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"home page", response.data)

    @patch("app_flask.render_template")
    def test_login_get(self, mock_render):
        mock_render.return_value = "login page"

        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"login page", response.data)

    @patch("app_flask.verify_user_login")
    @patch("app_flask.render_template")
    def test_login_post_invalid_user(self, mock_render, mock_verify):
        mock_verify.return_value = None
        mock_render.return_value = "login page"

        response = self.client.post(
            "/login",
            data={"email": "test@example.com", "password": "wrong"}
        )

        self.assertEqual(response.status_code, 200)

    @patch("app_flask.verify_user_login")
    def test_login_post_success(self, mock_verify):
        mock_verify.return_value = {
            "user_id": 1,
            "email": "test@example.com",
            "full_name": "Test User"
        }

        response = self.client.post(
            "/login",
            data={
                "email": "test@example.com",
                "password": "password123",
                "remember_me": "1"
            },
            follow_redirects=False
        )

        self.assertEqual(response.status_code, 302)

    def test_logout(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        response = self.client.get("/logout")

        self.assertEqual(response.status_code, 302)

    def test_favourite_page_redirect_when_not_logged_in(self):
        response = self.client.get("/favourite")

        self.assertEqual(response.status_code, 302)

    @patch("app_flask.render_template")
    def test_favourite_page_logged_in(self, mock_render):
        mock_render.return_value = "favourites page"

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        response = self.client.get("/favourite")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"favourites page", response.data)

    @patch("app_flask.render_template")
    def test_signup_get(self, mock_render):
        mock_render.return_value = "signup page"

        response = self.client.get("/signup")

        self.assertEqual(response.status_code, 200)

    @patch("app_flask.create_user")
    def test_signup_post_success(self, mock_create_user):
        mock_create_user.return_value = True

        response = self.client.post(
            "/signup",
            data={
                "full_name": "Test User",
                "email": "test@example.com",
                "password": "password123",
                "confirm_password": "password123",
            }
        )

        self.assertEqual(response.status_code, 302)

    @patch("app_flask.render_template")
    def test_signup_post_password_mismatch(self, mock_render):
        mock_render.return_value = "signup page"

        response = self.client.post(
            "/signup",
            data={
                "full_name": "Test User",
                "email": "test@example.com",
                "password": "password123",
                "confirm_password": "different",
            }
        )

        self.assertEqual(response.status_code, 200)

    @patch("app_flask.render_template")
    @patch("app_flask.request_current_weather")
    @patch("app_flask.request_hourly_forecast")
    @patch("app_flask.request_daily_forecast")
    def test_weather_page(
        self,
        mock_daily,
        mock_hourly,
        mock_weather,
        mock_render
    ):
        mock_weather.return_value = {}
        mock_hourly.return_value = []
        mock_daily.return_value = []
        mock_render.return_value = "weather page"

        response = self.client.get("/weather")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"weather page", response.data)


class CategorizedTestResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.category_stats = {
            "Environment": {"total": 0, "passes": 0, "fails": 0},
            "Configuration": {"total": 0, "passes": 0, "fails": 0},
            "Helper function": {"total": 0, "passes": 0, "fails": 0},
            "API endpoint": {"total": 0, "passes": 0, "fails": 0},
            "Other test": {"total": 0, "passes": 0, "fails": 0},
        }

    def get_category(self, test):
        test_name = test.id().lower()

        if "database" in test_name or "engine" in test_name or "connection" in test_name:
            return "Environment"

        if (
            "invalid" in test_name
            or "missing" in test_name
            or "failure" in test_name
            or "wrong" in test_name
            or "not_logged_in" in test_name
            or "not_found" in test_name
            or "empty" in test_name
        ):
            return "Configuration"

        if (
            "helper" in test_name
            or "score" in test_name
            or "label" in test_name
            or "haversine" in test_name
            or "nearest" in test_name
            or "build_context" in test_name
        ):
            return "Helper function"

        if (
            "api" in test_name
            or "route" in test_name
            or "flask" in test_name
            or "page" in test_name
            or "login" in test_name
            or "signup" in test_name
            or "logout" in test_name
            or "favourite" in test_name
        ):
            return "API endpoint"

        return "Other test"

    def startTest(self, test):
        super().startTest(test)
        category = self.get_category(test)
        self.category_stats[category]["total"] += 1

    def addSuccess(self, test):
        super().addSuccess(test)
        category = self.get_category(test)
        self.category_stats[category]["passes"] += 1

    def addFailure(self, test, err):
        super().addFailure(test, err)
        category = self.get_category(test)
        self.category_stats[category]["fails"] += 1

    def addError(self, test, err):
        super().addError(test, err)
        category = self.get_category(test)
        self.category_stats[category]["fails"] += 1


class CategorizedTestRunner(unittest.TextTestRunner):
    resultclass = CategorizedTestResult

    def run(self, test):
        result = super().run(test)

        print("\n" + "=" * 70)
        print("TEST SUMMARY BY CATEGORY")
        print("=" * 70)

        total_tests = 0
        total_passes = 0
        total_fails = 0

        print(f"{'Test category':<20} {'Total':<10} {'Passes':<10} {'Fails':<10} {'Success'}")
        print("-" * 70)

        for category, stats in result.category_stats.items():
            total = stats["total"]
            passes = stats["passes"]
            fails = stats["fails"]

            success_rate = (passes / total * 100) if total > 0 else 0

            total_tests += total
            total_passes += passes
            total_fails += fails

            print(
                f"{category:<20} "
                f"{total:<10} "
                f"{passes:<10} "
                f"{fails:<10} "
                f"{success_rate:.2f}%"
            )

        print("-" * 70)

        overall_success = (total_passes / total_tests * 100) if total_tests > 0 else 0

        print(
            f"{'Overall':<20} "
            f"{total_tests:<10} "
            f"{total_passes:<10} "
            f"{total_fails:<10} "
            f"{overall_success:.2f}%"
        )

        print("=" * 70)

        return result


if __name__ == "__main__":
    unittest.main(
        testRunner=CategorizedTestRunner(verbosity=2),
        verbosity=2
    )