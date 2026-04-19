import time
import logging
import traceback
import os
from component_py_file import db_operations, data_scraping

#create error_logs folder for saving error logs
os.makedirs("error_logs", exist_ok=True)

# logging setup
logging.basicConfig(
    filename="error_logs/error_log_data_weather.txt",
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def run_weather():

    db_operations.init_db()
    db_operations.init_weather_table()

    # intervals (seconds)
    CURRENT_EVERY = 5 * 60        # 5 minutes
    HOURLY_EVERY  = 15 * 60       # 15 minutes
    DAILY_EVERY   = 6 * 60 * 60   # 6 hours

    # run immediately at startup
    now = time.time()
    next_current = now
    next_hourly = now
    next_daily = now

    while True:
        now = time.time()

        # daily (every 6 hours)
        if now >= next_daily:
            try:
                data = data_scraping.fetch_weather_forecast_data_daily()
                db_operations.insert_weather_forecast_daily(data)
                print("daily success")
            except Exception:
                logging.error("Daily forecast error:\n%s", traceback.format_exc())
            next_daily = now + DAILY_EVERY

        # hourly forecast (every 15 minutes)
        if now >= next_hourly:
            try:
                data = data_scraping.fetch_weather_forecast_data_hourly()
                db_operations.insert_weather_forecast_hourly(data)
                print("hourly success")
            except Exception:
                logging.error("Hourly forecast error:\n%s", traceback.format_exc())
            next_hourly = now + HOURLY_EVERY

        # current (every 5 minutes)
        if now >= next_current:
            try:
                data = data_scraping.fetch_weather_current_data()
                db_operations.insert_weather_current_table(data)
                print("current success")
            except Exception:
                logging.error("Current weather error:\n%s", traceback.format_exc())
            next_current = now + CURRENT_EVERY

        # small sleep to avoid busy loop
        time.sleep(300)


if __name__ == "__main__":
    run_weather()

