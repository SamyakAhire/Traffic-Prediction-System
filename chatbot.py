from model import predict, best_time, peak_hours, traffic_trend
from datetime import datetime
import re
from utils import suggestion, alert
import pytz

# Memory (context)
context = {"location": "Hinjewadi", "weather": "Clear", "day": "Weekday", "hour": None}

def get_ist_hour():
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).hour

def extract_hour(msg):
    # handles "5", "5 pm", "17", "10am"
    match = re.search(r"(\d{1,2})\s*(am|pm)?", msg)
    if match:
        hour = int(match.group(1))
        if match.group(2) == "pm" and hour < 12:
            hour += 12
        if 0 <= hour <= 23:
            return hour
    return None


def chatbot_response(msg):
    msg = msg.lower()

    global context

    # Location detection
    locations = ["hinjewadi", "wakad", "baner", "kothrud", "shivajinagar", "swargate"]
    for loc in locations:
        if loc in msg:
            context["location"] = loc.capitalize()

    # Weather detection
    if "rain" in msg:
        context["weather"] = "Rain"
    elif "clear" in msg:
        context["weather"] = "Clear"

    # Day detection
    if "weekend" in msg:
        context["day"] = "Weekend"
    elif "weekday" in msg:
        context["day"] = "Weekday"

    # Time detection
    extracted_hour = extract_hour(msg)
    if extracted_hour is not None:
        context["hour"] = extracted_hour

    # default hour
    hour = context["hour"] if context["hour"] is not None else get_ist_hour()

    loc = context["location"]
    weather = context["weather"]
    day = context["day"]

    # INTENTS

    # Greeting
    if any(word in msg for word in ["hi", "hello", "hey"]):
        return f"👋 Hey! I'm your Traffic Buddy 🚦\nCurrently tracking traffic in {loc}.\nAsk me anything!"

    # Help
    if "help" in msg:
        return (
            "💡 Try asking:\n"
            "• Traffic now in Wakad\n"
            "• Best time to travel\n"
            "• Peak hours in Baner\n"
            "• Traffic at 5 pm\n"
            "• Is it busy now?"
        )

    # Traffic / congestion
    if any(word in msg for word in ["traffic", "now", "busy", "jam", "congestion"]):
        level, veh, conf = predict(hour, loc, weather, day)

        tip = (
            "✅ Good time to travel!"
            if level == "Low"
            else (
                "⚠️ Moderate traffic, plan accordingly."
                if level == "Medium"
                else "🚫 Heavy traffic! Avoid if possible."
            )
        )
        
        return (
            f"🚦 Traffic in {loc} at {hour}:00\n"
            f"• Level: {level}\n"
            f"• Vehicles: ~{veh}\n"
            f"• Confidence: {conf}%\n"
            f"{suggestion(level)}\n"
            f"{alert(level)}"
        )

    # Best time
    if "best" in msg:
        bt = best_time(loc, weather, hour, day)
        return f"✅ Best time to travel in {loc} is around {bt}:00 🚗"

    # Peak hours
    if "peak" in msg:
        peaks = peak_hours(loc)
        return f"⚠️ Peak hours in {loc}: {', '.join(map(str, peaks.keys()))}"

    # Trend
    if "trend" in msg or "pattern" in msg:
        peak, low = traffic_trend(loc)
        return f"📊 Traffic trend in {loc}:\n🔴 Peak: {peak}:00\n🟢 Low: {low}:00"

    # Recommendation
    if "should i go" in msg or "good time" in msg:
        level, _, _ = predict(hour, loc, weather, day)
        if level == "Low":
            return "✅ Yes, it's a great time to travel!"
        elif level == "Medium":
            return "⚠️ You can go, but expect some traffic."
        else:
            return "🚫 Not recommended right now, heavy congestion."

    # Context summary
    if "status" in msg:
        return (
            f"📍 Location: {loc}\n"
            f"🌦 Weather: {weather}\n"
            f"📅 Day: {day}\n"
            f"⏰ Time: {hour}:00"
        )
    if "tomorrow" in msg:
        return "📅 I can predict only today’s traffic for now."
    
    return (
        "🤖 I didn't understand.\n"
        "Try: 'traffic now', 'best time', 'peak hours', or 'help'"
    )
