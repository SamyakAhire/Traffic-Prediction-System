from flask import Flask, render_template, request, jsonify
from model import predict, best_time, peak_hours, traffic_trend, df_original
from datetime import datetime
from utils import suggestion, alert
from datetime import datetime
import pytz

def get_ist_hour():
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).hour

app = Flask(__name__)

@app.route("/")
def home():
    locations = df_original["Location"].unique().tolist()
    return render_template("index.html", locations=locations)

@app.route("/predict")
def get_prediction():
    try:
        hour = request.args.get("hour")
        location = request.args.get("location")
        weather = request.args.get("weather")
        day = request.args.get("day")

        if not location:
            return jsonify({"error": "Location required"}), 400

        if not weather:
            weather = "Clear"

        if not day:
            day = "Weekday"

        if hour == "now":
            hour = get_ist_hour()

        else:
            if not hour:
                return jsonify({"error": "Enter hour"}), 400

            hour = int(hour)

            if hour < 0 or hour > 23:
                return jsonify({"error": "Hour must be 0-23"}), 400

        level, vehicles, conf = predict(hour, location, weather, day)

        peak = peak_hours(location)
        trend_peak, trend_low = traffic_trend(location)

        return jsonify({
            "hour": hour,
            "congestion": level,
            "vehicles": vehicles,
            "confidence": conf,
            "suggestion": suggestion(level),
            "alert": alert(level),
            "best_time": best_time(location, weather, hour, day),
            "peak_hours": peak,
            "trend_peak": trend_peak,
            "trend_low": trend_low
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/data")
def data():
    location = request.args.get("location")

    df_local = df_original.copy()

    if location:
        df_local = df_local[df_local["Location"] == location]

    if df_local.empty:
        return jsonify({i: 0 for i in range(24)})

    result = df_local.groupby("Hour")["Vehicle_Count"].mean()

    data = {int(k): float(v) for k, v in result.items()}

    return jsonify(data)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"reply": "Please send a message."})

        from chatbot import chatbot_response
        reply = chatbot_response(data["message"])

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": "Error processing request"})

if __name__ == "__main__":
    app.run(debug=True)