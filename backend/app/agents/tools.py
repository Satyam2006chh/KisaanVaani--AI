import httpx
from app.config import settings

# WMO weather code to Hindi description
WMO_CODES = {
    0: "Saaf aasman", 1: "Zyaadatar saaf", 2: "Aansik badal", 3: "Badal chhaye hain",
    45: "Kohra", 48: "Barf wala kohra",
    51: "Halki boondi", 53: "Boondi", 55: "Tej boondi",
    61: "Halki baarish", 63: "Baarish", 65: "Tej baarish",
    71: "Halki barf", 73: "Barf", 75: "Tej barf",
    80: "Halki bauchhar", 81: "Bauchhar", 82: "Tej bauchhar",
    95: "Aandhi toofan", 99: "Toofan aur ole",
}

# Real MSP (Minimum Support Price) 2024-25 data from Govt of India
MSP_DATA = {
    "wheat": {"hindi": "Gehun", "msp": 2275, "unit": "quintal"},
    "gehun": {"hindi": "Gehun", "msp": 2275, "unit": "quintal"},
    "rice": {"hindi": "Dhan/Chawal", "msp": 2300, "unit": "quintal"},
    "dhan": {"hindi": "Dhan", "msp": 2300, "unit": "quintal"},
    "paddy": {"hindi": "Dhan", "msp": 2300, "unit": "quintal"},
    "mustard": {"hindi": "Sarson", "msp": 5950, "unit": "quintal"},
    "sarson": {"hindi": "Sarson", "msp": 5950, "unit": "quintal"},
    "maize": {"hindi": "Makka", "msp": 2225, "unit": "quintal"},
    "makka": {"hindi": "Makka", "msp": 2225, "unit": "quintal"},
    "soybean": {"hindi": "Soyabean", "msp": 4892, "unit": "quintal"},
    "cotton": {"hindi": "Kapas", "msp": 7521, "unit": "quintal"},
    "kapas": {"hindi": "Kapas", "msp": 7521, "unit": "quintal"},
    "bajra": {"hindi": "Bajra", "msp": 2625, "unit": "quintal"},
    "jowar": {"hindi": "Jowar", "msp": 3371, "unit": "quintal"},
    "groundnut": {"hindi": "Moongfali", "msp": 6783, "unit": "quintal"},
    "moongfali": {"hindi": "Moongfali", "msp": 6783, "unit": "quintal"},
    "sunflower": {"hindi": "Surajmukhi", "msp": 7280, "unit": "quintal"},
    "gram": {"hindi": "Chana", "msp": 5440, "unit": "quintal"},
    "chana": {"hindi": "Chana", "msp": 5440, "unit": "quintal"},
    "lentil": {"hindi": "Masoor", "msp": 6425, "unit": "quintal"},
    "masoor": {"hindi": "Masoor", "msp": 6425, "unit": "quintal"},
    "moong": {"hindi": "Moong", "msp": 8682, "unit": "quintal"},
    "urad": {"hindi": "Urad", "msp": 7400, "unit": "quintal"},
    "sugarcane": {"hindi": "Ganna", "msp": 340, "unit": "quintal"},
    "ganna": {"hindi": "Ganna", "msp": 340, "unit": "quintal"},
}


async def get_weather(district: str, state: str) -> str:
    """Fetch real weather using Open-Meteo (free, no API key needed)."""
    try:
        # Step 1: Geocode district name to lat/lon
        async with httpx.AsyncClient(timeout=10) as client:
            geo = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": district, "count": 1, "language": "en", "format": "json"}
            )

        if geo.status_code != 200 or not geo.json().get("results"):
            return f"{district} ka mausam abhi uplabdh nahi hai."

        loc = geo.json()["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]

        # Step 2: Get current weather
        async with httpx.AsyncClient(timeout=10) as client:
            weather = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat, "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                    "timezone": "Asia/Kolkata",
                    "forecast_days": 1,
                }
            )

        if weather.status_code != 200:
            return f"{district} ka mausam abhi uplabdh nahi hai."

        data = weather.json()
        cur = data["current"]
        daily = data.get("daily", {})

        temp     = cur["temperature_2m"]
        humidity = cur["relative_humidity_2m"]
        wind     = cur["wind_speed_10m"]
        rain     = cur["precipitation"]
        code     = cur["weather_code"]
        desc     = WMO_CODES.get(code, "Mausam saaf hai")
        max_t    = daily.get("temperature_2m_max", [temp])[0]
        min_t    = daily.get("temperature_2m_min", [temp])[0]

        result = (
            f"{district}, {state} mein abhi {temp}°C temperature hai (Max: {max_t}°C, Min: {min_t}°C). "
            f"Mausam: {desc}. "
            f"Namee (Humidity): {humidity}%. "
            f"Hawa ki gati: {wind} km/h. "
        )
        if rain > 0:
            result += f"Aaj {rain}mm baarish hui hai. "

        # Farming tip based on weather
        if code in [61, 63, 65, 80, 81, 82]:
            result += "Aaj khet mein kaam karna mushkil ho sakta hai, baarish ho rahi hai."
        elif temp > 40:
            result += "Bahut garmi hai, fasal ko zyada paani dein."
        elif temp < 10:
            result += "Thandi bahut hai, pala padne ka darr hai, fasal ko bachayein."
        else:
            result += "Mausam kheti ke liye theek hai."

        return result

    except Exception as e:
        return f"{district} ka mausam abhi uplabdh nahi hai."


async def get_mandi_price(crop: str, district: str) -> str:
    """Return MSP + market price context using hardcoded Govt MSP 2024-25 data."""
    crop_lower = crop.lower().strip()

    # Find crop in MSP data
    info = MSP_DATA.get(crop_lower)
    if not info:
        # Try partial match
        for key, val in MSP_DATA.items():
            if key in crop_lower or crop_lower in key:
                info = val
                break

    if not info:
        return (
            f"{crop} ka MSP data abhi uplabdh nahi hai. "
            f"Apne nazdiki mandi ya Agmarknet (agmarknet.nic.in) par check karein."
        )

    msp = info["msp"]
    name = info["hindi"]
    # Typical market price is 5-15% above MSP
    market_low  = int(msp * 1.02)
    market_high = int(msp * 1.12)

    return (
        f"{district} mein {name} ke bhav:\n"
        f"  Sarkari MSP (2024-25): Rs {msp} per quintal\n"
        f"  Mandi market bhav (anumaan): Rs {market_low} - {market_high} per quintal\n"
        f"  Sahi bhav ke liye Agmarknet (agmarknet.nic.in) ya apni nazdiki mandi check karein.\n"
        f"  Tip: MSP se kam mein mat bechein, yeh aapka adhikar hai."
    )
