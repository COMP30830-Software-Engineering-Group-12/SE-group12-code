import pandas as pd

df = pd.read_csv("bike_weather_data.csv")

print("Shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())

print("\nMissing values:")
print(df.isnull().sum())

print("\nUnique stations:", df["station_id"].nunique() if "station_id" in df.columns else "missing")
