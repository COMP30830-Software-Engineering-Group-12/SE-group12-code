import time
import logging
import traceback
import os
from component_py_file import db_operations, data_scraping

#create error_logs folder for saving error logs
os.makedirs("error_logs", exist_ok=True)

# logging setup
logging.basicConfig(
    filename="error_logs/error_log_data_bike.txt",
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

def run_bike():
    db_operations.init_db()
    db_operations.init_bike__table()
    while True:
        try:
            data = data_scraping.fetch_bike_data()
            db_operations.insert_bike__table(data)
        except Exception:
            logging.error("Bike job error:\n%s", traceback.format_exc())
        time.sleep(300)


if __name__ == "__main__":
    run_bike()