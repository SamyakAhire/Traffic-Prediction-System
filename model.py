import pandas as pd
import random
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Load dataset
df_original = pd.read_csv("data/pune_traffic_dataset_with_weather.csv")
df = df_original.copy()

# Encoders
le_location = LabelEncoder()
le_weather = LabelEncoder()
le_congestion = LabelEncoder()
le_day = LabelEncoder()

# Encoding
df["Location"] = le_location.fit_transform(df["Location"])

df["Weather"] = df["Weather"].fillna("Clear")
df["Weather"] = le_weather.fit_transform(df["Weather"])

df["Day_Type"] = le_day.fit_transform(df["Day_Type"])
df["Congestion_Level"] = le_congestion.fit_transform(df["Congestion_Level"])

# Feature Engineering
df["Is_Peak"] = df["Hour"].apply(lambda x: 1 if 7<=x<=10 or 17<=x<=20 else 0)

X = df[["Hour","Location","Weather","Day_Type","Is_Peak"]]
y = df["Congestion_Level"]

# Train once
try:
    model = joblib.load("model.pkl")
except:
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)
    joblib.dump(model, "model.pkl")

# Encoders
def encode_location(loc):
    return le_location.transform([loc])[0] if loc in le_location.classes_ else 0

def encode_weather(w):
    return le_weather.transform([w])[0] if w in le_weather.classes_ else 0

def encode_day(d):
    return le_day.transform([d])[0] if d in le_day.classes_ else 0

# Prediction
def predict(hour, location, weather, day):
    loc = encode_location(location)
    wea = encode_weather(weather)
    d = encode_day(day)

    is_peak = 1 if 7<=hour<=10 or 17<=hour<=20 else 0

    pred = model.predict([[hour, loc, wea, d, is_peak]])[0]
    probs = model.predict_proba([[hour, loc, wea, d, is_peak]])[0]

    level = le_congestion.inverse_transform([pred])[0]
    confidence = round(max(probs)*100,2)

    subset = df[(df["Location"]==loc)&(df["Hour"]==hour)]
    vehicles = max(10, int(subset["Vehicle_Count"].mean())) if not subset.empty else random.randint(50,150)

    return level, vehicles, confidence

# Best time (future-aware)
def best_time(location, weather, hour, day):
    loc = encode_location(location)
    wea = encode_weather(weather)
    d = encode_day(day)

    filtered = df[(df["Location"]==loc)&(df["Weather"]==wea)&(df["Day_Type"]==d)]

    if filtered.empty:
        return "No data"

    avg = filtered.groupby("Hour")["Vehicle_Count"].mean()
    future = avg[avg.index > hour]

    return int(future.idxmin()) if not future.empty else f"Tomorrow {int(avg.idxmin())}"

# Peak hours
def peak_hours(location):
    loc = encode_location(location)
    avg = df[df["Location"]==loc].groupby("Hour")["Vehicle_Count"].mean()
    return avg.sort_values(ascending=False).head(3).to_dict()

# Trend
def traffic_trend(location):
    loc = encode_location(location)
    avg = df[df["Location"]==loc].groupby("Hour")["Vehicle_Count"].mean()
    return int(avg.idxmax()), int(avg.idxmin())