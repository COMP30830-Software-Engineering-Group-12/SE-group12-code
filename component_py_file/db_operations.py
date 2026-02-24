from . import dbinfo
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from datetime import datetime, timedelta, timezone

def init_db():
    # connect without specifying a DB, so we can CREATE DATABASE
    url = URL.create(
        drivername="mysql+pymysql",
        username=dbinfo.sqlusername,
        password=dbinfo.sqlpassword,
        host=dbinfo.sqlurl,
        port=dbinfo.sqlport,
    )
    engine = create_engine(url, echo=False, pool_pre_ping=True)

    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE DATABASE IF NOT EXISTS `{dbinfo.db_name}`
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_0900_ai_ci;
        """))

def init_bike__table():
    db_url = URL.create(
        drivername="mysql+pymysql",
        username=dbinfo.sqlusername,
        password=dbinfo.sqlpassword,
        host=dbinfo.sqlurl,
        port=dbinfo.sqlport,
        database=dbinfo.db_name,
    )
    engine = create_engine(db_url, echo=False, pool_pre_ping=True)

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `bike_station` (
              station_number INT NOT NULL,
              contract_name VARCHAR(64) NOT NULL,
              name VARCHAR(128) NOT NULL,
              address VARCHAR(255) DEFAULT NULL,
              station_lat DECIMAL(9,6) NOT NULL,
              station_lon DECIMAL(9,6) NOT NULL,
              capacity INT NOT NULL,
              PRIMARY KEY (station_number),
              INDEX idx_bike_station_contract (contract_name),
              INDEX idx_bike_station_geo (station_lat, station_lon)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `bike_station_status` (
              id BIGINT NOT NULL AUTO_INCREMENT,
              station_number INT NOT NULL,
              time_updated DATETIME NOT NULL,
              status VARCHAR(16) NOT NULL,
              available_bikes INT NOT NULL,
              available_stands INT NOT NULL,
              PRIMARY KEY (id),
              UNIQUE KEY uq_station_time (station_number, time_updated),
              INDEX idx_time_updated (time_updated),
              INDEX idx_station_time (station_number, time_updated),
              CONSTRAINT fk_status_station
                FOREIGN KEY (station_number)
                REFERENCES bike_station (station_number)
                ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))


def insert_bike__table(data):
    """
    data: list[dict]
    Writes:
      - bike_station
      - bike_station_status
    Keeps only last 48 hours in bike_station_status.
    """

    # connect to schema
    db_url = URL.create(
        drivername="mysql+pymysql",
        username=dbinfo.sqlusername,
        password=dbinfo.sqlpassword,
        host=dbinfo.sqlurl,
        port=dbinfo.sqlport,
        database=dbinfo.db_name,
    )
    engine = create_engine(db_url, pool_pre_ping=True, echo=False)

    # prepare rows
    station_rows = []
    status_rows = []

    for s in data:
        station_number = int(s["number"])
        contract_name = s.get("contract_name", "")
        name = s.get("name", "")
        address = s.get("address")
        lat = float(s["position"]["lat"])
        lon = float(s["position"]["lng"])
        capacity = int(s.get("bike_stands", 0))

        # last_update in your sample is milliseconds since epoch  [oai_citation:1‡bike_data.txt](sediment://file_00000000eca87246a15634a23c31af78)
        last_update_ms = s.get("last_update")
        if last_update_ms is None:
            # if missing, use "now" UTC
            observed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            observed_at = datetime.fromtimestamp(last_update_ms / 1000, tz=timezone.utc).replace(tzinfo=None)

        status = s.get("status", "")
        available_bikes = int(s.get("available_bikes", 0))
        available_stands = int(s.get("available_bike_stands", 0))

        station_rows.append({
            "station_number": station_number,
            "contract_name": contract_name,
            "name": name,
            "address": address,
            "station_lat": lat,
            "station_lon": lon,
            "capacity": capacity,
        })

        status_rows.append({
            "station_number": station_number,
            "time_updated": observed_at,
            "status": status,
            "available_bikes": available_bikes,
            "available_stands": available_stands,
        })

    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)

    with engine.begin() as conn:
        # 1) upsert into bike_station
        conn.execute(
            text("""
                INSERT INTO bike_station
                (station_number, contract_name, name, address, station_lat, station_lon, capacity)
                VALUES
                (:station_number, :contract_name, :name, :address, :station_lat, :station_lon, :capacity)
                ON DUPLICATE KEY UPDATE
                    contract_name = VALUES(contract_name),
                    name = VALUES(name),
                    address = VALUES(address),
                    station_lat = VALUES(station_lat),
                    station_lon = VALUES(station_lon),
                    capacity = VALUES(capacity);
            """),
            station_rows
        )

        # 2) insert into bike_station_status (dedupe by UNIQUE(station_number, time_updated))
        # If you prefer "ignore duplicates" rather than updating them, this is clean.
        conn.execute(
            text("""
                INSERT INTO bike_station_status
                (station_number, time_updated, status, available_bikes, available_stands)
                VALUES
                (:station_number, :time_updated, :status, :available_bikes, :available_stands)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    available_bikes = VALUES(available_bikes),
                    available_stands = VALUES(available_stands);
            """),
            status_rows
        )

        # 3) keep only last 48 hours
        conn.execute(
            text("""
                DELETE FROM bike_station_status
                WHERE time_updated < :cutoff;
            """),
            {"cutoff": cutoff}
        )


def init_weather_table():

    # connect to schema
    db_url = URL.create(
        drivername="mysql+pymysql",
        username=dbinfo.sqlusername,
        password=dbinfo.sqlpassword,
        host=dbinfo.sqlurl,
        port=dbinfo.sqlport,
        database=dbinfo.db_name,
    )
    engine = create_engine(db_url, pool_pre_ping=True, echo=False)

    with engine.begin() as conn:
        # weather_current table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS weather_current (
                weather_current_id BIGINT NOT NULL AUTO_INCREMENT,
                time_updated DATETIME NOT NULL,
                weather_id INT,
                weather_main VARCHAR(32),
                weather_description VARCHAR(64),
                weather_icon VARCHAR(8),
                temp FLOAT NOT NULL,
                feels_like FLOAT,
                temp_min FLOAT,
                temp_max FLOAT,
                pressure INT,
                humidity INT,
                visibility INT,
                wind_speed FLOAT,
                wind_deg INT,
                clouds INT,
                sunrise DATETIME,
                sunset DATETIME,
                PRIMARY KEY (weather_current_id),
                UNIQUE KEY uq_current_time (time_updated),
                INDEX idx_weather_current_time (time_updated)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))

        # weather_forecast_hourly table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS weather_forecast_hourly (
                weather_forecast_hourly_id BIGINT NOT NULL AUTO_INCREMENT,
                time_forecast DATETIME NOT NULL,
                dt_txt DATETIME,
                weather_id INT,
                weather_main VARCHAR(32),
                weather_description VARCHAR(64),
                weather_icon VARCHAR(8),
                temp FLOAT NOT NULL,
                feels_like FLOAT,
                temp_min FLOAT,
                temp_max FLOAT,
                pressure INT,
                humidity INT,
                visibility INT,
                wind_speed FLOAT,
                wind_deg INT,
                clouds INT,
                pop FLOAT,
                rain_1h FLOAT,
                PRIMARY KEY (weather_forecast_hourly_id),
                UNIQUE KEY uq_forecast_time (time_forecast),
                INDEX idx_weather_forecast_time (time_forecast),
                INDEX idx_weather_forecast_dt_txt (dt_txt)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))

        # weather_forecast_daily
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS weather_forecast_daily (
                weather_forecast_daily_id BIGINT NOT NULL AUTO_INCREMENT,
                time_forecast DATETIME NOT NULL,
                sunrise DATETIME,
                sunset DATETIME,
                temp_morn FLOAT,
                temp_day FLOAT,
                temp_eve FLOAT,
                temp_min FLOAT,
                temp_max FLOAT,
                feels_like_morn FLOAT,
                feels_like_day FLOAT,
                feels_like_eve FLOAT,
                feels_like_night FLOAT,
                pressure INT,
                humidity INT,
                weather_id INT,
                weather_main VARCHAR(32),
                weather_description VARCHAR(64),
                weather_icon VARCHAR(8),
                wind_speed FLOAT,
                wind_deg INT,
                clouds INT,
                pop FLOAT,
                rain FLOAT,
                PRIMARY KEY (weather_forecast_daily_id),
                UNIQUE KEY uq_daily_time (time_forecast),
                INDEX idx_daily_time (time_forecast)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))

#inserting current weather data
def insert_weather_current_table(data: dict):
    """
    Insert/Upsert one OpenWeather 'current weather' JSON into weather_current table,
    and keep only last 48 hours.

    Assumptions:
      - weather_current has UNIQUE KEY uq_current_time (time_updated)
      - time_updated stored as UTC naive DATETIME
    """

    # connect to schema
    db_url = URL.create(
        drivername="mysql+pymysql",
        username=dbinfo.sqlusername,
        password=dbinfo.sqlpassword,
        host=dbinfo.sqlurl,
        port=dbinfo.sqlport,
        database=dbinfo.db_name,
    )
    engine = create_engine(db_url, pool_pre_ping=True, echo=False)

    def ts_to_utc_naive(ts: int | None) -> datetime | None:
        if ts is None:
            return None
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).replace(tzinfo=None)

    # --- Parse OpenWeather JSON (see sample structure)  [oai_citation:1‡weather_current_data.txt](sediment://file_0000000071a87246b6001af855ba7f5e)
    w0 = (data.get("weather") or [{}])[0]  # first weather entry

    time_updated = ts_to_utc_naive(data.get("dt"))
    if time_updated is None:
        # fallback: "now" in UTC if dt missing
        time_updated = datetime.now(timezone.utc).replace(tzinfo=None)

    main = data.get("main") or {}
    wind = data.get("wind") or {}
    clouds = data.get("clouds") or {}
    sys = data.get("sys") or {}

    row = {
        "time_updated": time_updated,
        "weather_id": w0.get("id"),
        "weather_main": w0.get("main"),
        "weather_description": w0.get("description"),
        "weather_icon": w0.get("icon"),

        "temp": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "temp_min": main.get("temp_min"),
        "temp_max": main.get("temp_max"),

        "pressure": main.get("pressure"),
        "humidity": main.get("humidity"),
        "visibility": data.get("visibility"),

        "wind_speed": wind.get("speed"),
        "wind_deg": wind.get("deg"),

        "clouds": clouds.get("all"),

        "sunrise": ts_to_utc_naive(sys.get("sunrise")),
        "sunset": ts_to_utc_naive(sys.get("sunset")),
    }

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).replace(tzinfo=None)

    with engine.begin() as conn:
        # Upsert (won't error on duplicate time_updated)
        conn.execute(
            text("""
                INSERT INTO weather_current (
                    time_updated,
                    weather_id, weather_main, weather_description, weather_icon,
                    temp, feels_like, temp_min, temp_max,
                    pressure, humidity, visibility,
                    wind_speed, wind_deg,
                    clouds,
                    sunrise, sunset
                )
                VALUES (
                    :time_updated,
                    :weather_id, :weather_main, :weather_description, :weather_icon,
                    :temp, :feels_like, :temp_min, :temp_max,
                    :pressure, :humidity, :visibility,
                    :wind_speed, :wind_deg,
                    :clouds,
                    :sunrise, :sunset
                )
                ON DUPLICATE KEY UPDATE
                    weather_id = VALUES(weather_id),
                    weather_main = VALUES(weather_main),
                    weather_description = VALUES(weather_description),
                    weather_icon = VALUES(weather_icon),
                    temp = VALUES(temp),
                    feels_like = VALUES(feels_like),
                    temp_min = VALUES(temp_min),
                    temp_max = VALUES(temp_max),
                    pressure = VALUES(pressure),
                    humidity = VALUES(humidity),
                    visibility = VALUES(visibility),
                    wind_speed = VALUES(wind_speed),
                    wind_deg = VALUES(wind_deg),
                    clouds = VALUES(clouds),
                    sunrise = VALUES(sunrise),
                    sunset = VALUES(sunset);
            """),
            row
        )

        # Keep only last 48 hours
        conn.execute(
            text("""
                DELETE FROM weather_current
                WHERE time_updated < :cutoff;
            """),
            {"cutoff": cutoff}
        )



def insert_weather_forecast_hourly(data: dict):
    db_url = URL.create(
        drivername="mysql+pymysql",
        username=dbinfo.sqlusername,
        password=dbinfo.sqlpassword,
        host=dbinfo.sqlurl,
        port=dbinfo.sqlport,
        database=dbinfo.db_name,
    )
    engine = create_engine(db_url, pool_pre_ping=True, echo=False)

    def ts_to_utc_naive(ts: int | None):
        if ts is None:
            return None
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).replace(tzinfo=None)

    rows = []
    forecast_list = data.get("list", [])

    for item in forecast_list:
        main = item.get("main") or {}
        wind = item.get("wind") or {}
        clouds = item.get("clouds") or {}
        weather = (item.get("weather") or [{}])[0]
        rain = item.get("rain") or {}

        dt_txt = item.get("dt_txt")
        dt_txt_dt = (
            datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
            if dt_txt else None
        )

        rows.append({
            "time_forecast": ts_to_utc_naive(item.get("dt")),
            "dt_txt": dt_txt_dt,

            "weather_id": weather.get("id"),
            "weather_main": weather.get("main"),
            "weather_description": weather.get("description"),
            "weather_icon": weather.get("icon"),

            "temp": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "temp_min": main.get("temp_min"),
            "temp_max": main.get("temp_max"),

            "pressure": main.get("pressure"),
            "humidity": main.get("humidity"),
            "visibility": item.get("visibility"),

            "wind_speed": wind.get("speed"),
            "wind_deg": wind.get("deg"),

            "clouds": clouds.get("all"),

            "pop": item.get("pop"),

            # OpenWeather uses {"rain": {"1h": ...}} sometimes absent  [oai_citation:1‡weather_forecast_data_hourly.txt](sediment://file_00000000b888724681e408311797cca9)
            "rain_1h": rain.get("1h"),
        })

    if not rows:
        return

    # keep last 48h forecasts (relative to "now" UTC)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).replace(tzinfo=None)

    with engine.begin() as conn:
        # upsert by UNIQUE(time_forecast)
        conn.execute(
            text("""
                INSERT INTO weather_forecast_hourly (
                    time_forecast, dt_txt,
                    weather_id, weather_main, weather_description, weather_icon,
                    temp, feels_like, temp_min, temp_max,
                    pressure, humidity, visibility,
                    wind_speed, wind_deg,
                    clouds,
                    pop, rain_1h
                )
                VALUES (
                    :time_forecast, :dt_txt,
                    :weather_id, :weather_main, :weather_description, :weather_icon,
                    :temp, :feels_like, :temp_min, :temp_max,
                    :pressure, :humidity, :visibility,
                    :wind_speed, :wind_deg,
                    :clouds,
                    :pop, :rain_1h
                )
                ON DUPLICATE KEY UPDATE
                    dt_txt = VALUES(dt_txt),
                    weather_id = VALUES(weather_id),
                    weather_main = VALUES(weather_main),
                    weather_description = VALUES(weather_description),
                    weather_icon = VALUES(weather_icon),
                    temp = VALUES(temp),
                    feels_like = VALUES(feels_like),
                    temp_min = VALUES(temp_min),
                    temp_max = VALUES(temp_max),
                    pressure = VALUES(pressure),
                    humidity = VALUES(humidity),
                    visibility = VALUES(visibility),
                    wind_speed = VALUES(wind_speed),
                    wind_deg = VALUES(wind_deg),
                    clouds = VALUES(clouds),
                    pop = VALUES(pop),
                    rain_1h = VALUES(rain_1h);
            """),
            rows
        )

        # delete forecasts older than 48 hours
        conn.execute(
            text("""
                DELETE FROM weather_forecast_hourly
                WHERE time_forecast < :cutoff;
            """),
            {"cutoff": cutoff}
        )



def insert_weather_forecast_daily(data: dict):
    """
    Insert/Upsert OpenWeather daily forecast JSON into weather_forecast_daily,
    and keep only last 48 hours by time_forecast.

    Assumptions:
      - weather_forecast_daily has UNIQUE KEY uq_daily_time (time_forecast)
      - time_forecast stored as UTC naive DATETIME
    """

    db_url = URL.create(
        drivername="mysql+pymysql",
        username=dbinfo.sqlusername,
        password=dbinfo.sqlpassword,
        host=dbinfo.sqlurl,
        port=dbinfo.sqlport,
        database=dbinfo.db_name,
    )
    engine = create_engine(db_url, pool_pre_ping=True, echo=False)

    def ts_to_utc_naive(ts: int | None):
        if ts is None:
            return None
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).replace(tzinfo=None)

    rows = []
    daily_list = data.get("list", [])

    for item in daily_list:
        temp = item.get("temp") or {}
        feels = item.get("feels_like") or {}
        weather = (item.get("weather") or [{}])[0]

        rows.append({
            "time_forecast": ts_to_utc_naive(item.get("dt")),
            "sunrise": ts_to_utc_naive(item.get("sunrise")),
            "sunset": ts_to_utc_naive(item.get("sunset")),

            "temp_morn": temp.get("morn"),
            "temp_day": temp.get("day"),
            "temp_eve": temp.get("eve"),
            "temp_min": temp.get("min"),
            "temp_max": temp.get("max"),

            "feels_like_morn": feels.get("morn"),
            "feels_like_day": feels.get("day"),
            "feels_like_eve": feels.get("eve"),
            "feels_like_night": feels.get("night"),

            "pressure": item.get("pressure"),
            "humidity": item.get("humidity"),

            "weather_id": weather.get("id"),
            "weather_main": weather.get("main"),
            "weather_description": weather.get("description"),
            "weather_icon": weather.get("icon"),

            # daily JSON uses "speed"/"deg" in your sample  [oai_citation:1‡weather_forecast_data_daily.txt](sediment://file_000000009d7c720a9cb204608ba140a5)
            "wind_speed": item.get("speed"),
            "wind_deg": item.get("deg"),

            "clouds": item.get("clouds"),

            "pop": item.get("pop"),
            "rain": item.get("rain"),
        })

    if not rows:
        return

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).replace(tzinfo=None)

    with engine.begin() as conn:
        # Upsert by UNIQUE(time_forecast)
        conn.execute(
            text("""
                INSERT INTO weather_forecast_daily (
                    time_forecast,
                    sunrise, sunset,

                    temp_morn, temp_day, temp_eve, temp_min, temp_max,
                    feels_like_morn, feels_like_day, feels_like_eve, feels_like_night,

                    pressure, humidity,

                    weather_id, weather_main, weather_description, weather_icon,

                    wind_speed, wind_deg,
                    clouds,

                    pop, rain
                )
                VALUES (
                    :time_forecast,
                    :sunrise, :sunset,

                    :temp_morn, :temp_day, :temp_eve, :temp_min, :temp_max,
                    :feels_like_morn, :feels_like_day, :feels_like_eve, :feels_like_night,

                    :pressure, :humidity,

                    :weather_id, :weather_main, :weather_description, :weather_icon,

                    :wind_speed, :wind_deg,
                    :clouds,

                    :pop, :rain
                )
                ON DUPLICATE KEY UPDATE
                    sunrise = VALUES(sunrise),
                    sunset = VALUES(sunset),

                    temp_morn = VALUES(temp_morn),
                    temp_day = VALUES(temp_day),
                    temp_eve = VALUES(temp_eve),
                    temp_min = VALUES(temp_min),
                    temp_max = VALUES(temp_max),

                    feels_like_morn = VALUES(feels_like_morn),
                    feels_like_day = VALUES(feels_like_day),
                    feels_like_eve = VALUES(feels_like_eve),
                    feels_like_night = VALUES(feels_like_night),

                    pressure = VALUES(pressure),
                    humidity = VALUES(humidity),

                    weather_id = VALUES(weather_id),
                    weather_main = VALUES(weather_main),
                    weather_description = VALUES(weather_description),
                    weather_icon = VALUES(weather_icon),

                    wind_speed = VALUES(wind_speed),
                    wind_deg = VALUES(wind_deg),

                    clouds = VALUES(clouds),

                    pop = VALUES(pop),
                    rain = VALUES(rain);
            """),
            rows
        )

        # Keep only last 48 hours
        conn.execute(
            text("""
                DELETE FROM weather_forecast_daily
                WHERE time_forecast < :cutoff;
            """),
            {"cutoff": cutoff}
        )