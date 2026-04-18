import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import math

CSV_FILE = "bike_weather_data.csv"
MODEL_FILE = "bike_availability_model.pkl"

FEATURES = [
    "station_id",
    "temperature",
    "humidity",
    "wind_speed",
    "precipitation",
    "hour",
    "day_of_week",
]

TARGET = "available_bikes"


def main():
    df = pd.read_csv(CSV_FILE)

    # Keep only needed columns
    df = df[FEATURES + [TARGET]].dropna()

    if len(df) < 20:
        raise ValueError("Not enough rows to train the model yet.")

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        max_depth=12
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    rmse = math.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)

    print("Random Forest Results:")
    print(f"Rows used: {len(df)}")
    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R²: {r2:.4f}")

    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)

    print(f"Saved model to {MODEL_FILE}")


if __name__ == "__main__":
    main()