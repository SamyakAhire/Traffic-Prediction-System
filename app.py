from flask import Flask, render_template, request, jsonify
from model import predict, best_time, peak_hours, traffic_trend, df_original
from datetime import datetime
from utils import suggestion, alert

app = Flask(__name__)

# ✅ Home
@app.route("/")
def home():
    locations = df_original["Location"].unique().tolist()
    return render_template("index.html", locations=locations)

# ✅ Prediction API
@app.route("/predict")
def get_prediction():
    try:
        hour = request.args.get("hour")
        location = request.args.get("location")
        weather = request.args.get("weather")
        day = request.args.get("day")

        # 🔥 Validate inputs
        if not location:
            return jsonify({"error": "Location required"}), 400

        if not weather:
            weather = "Clear"

        if not day:
            day = "Weekday"

        # ⏱ Real-time
        if hour == "now":
            hour = datetime.now().hour
        else:
            if not hour:
                return jsonify({"error": "Enter hour"}), 400

            hour = int(hour)

            if hour < 0 or hour > 23:
                return jsonify({"error": "Hour must be 0-23"}), 400

        # 🔥 Prediction
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


# ✅ Chart Data API (FIXED)
@app.route("/data")
def data():
    location = request.args.get("location")

    df_local = df_original.copy()

    if location:
        df_local = df_local[df_local["Location"] == location]

    if df_local.empty:
        return jsonify({i: 0 for i in range(24)})

    result = df_local.groupby("Hour")["Vehicle_Count"].mean()

    # 🔥 Convert keys to sorted list
    data = {int(k): float(v) for k, v in result.items()}

    return jsonify(data)


# ✅ Chatbot API (SAFE)
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


# ✅ Run
if __name__ == "__main__":
    app.run(debug=True)