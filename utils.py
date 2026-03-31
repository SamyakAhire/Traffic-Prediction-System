def suggestion(level):
    if level == "High":
        return "🚫 Heavy traffic! Avoid traveling now."
    elif level == "Medium":
        return "⚠️ Moderate traffic, expect delays."
    else:
        return "✅ Smooth traffic, good time to travel."

def alert(level):
    return "🔔 Alert: Heavy traffic detected!" if level == "High" else ""