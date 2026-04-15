import httpx

WMO_CODES = {
    0: "Saaf aasman", 1: "Zyaadatar saaf", 2: "Aansik badal", 3: "Badal chhaye hain",
    45: "Kohra", 48: "Barf wala kohra",
    51: "Halki boondi", 53: "Boondi", 55: "Tej boondi",
    61: "Halki baarish", 63: "Baarish", 65: "Tej baarish",
    71: "Halki barf", 73: "Barf", 75: "Tej barf",
    80: "Halki bauchhar", 81: "Bauchhar", 82: "Tej bauchhar",
    95: "Aandhi toofan", 99: "Toofan aur ole",
}

# Govt of India MSP 2024-25 (Rs per quintal)
MSP = {
    "wheat": ("Gehun", 2275), "gehun": ("Gehun", 2275),
    "rice": ("Dhan", 2300), "dhan": ("Dhan", 2300), "paddy": ("Dhan", 2300),
    "mustard": ("Sarson", 5950), "sarson": ("Sarson", 5950),
    "maize": ("Makka", 2225), "makka": ("Makka", 2225),
    "soybean": ("Soyabean", 4892), "soya": ("Soyabean", 4892),
    "cotton": ("Kapas", 7521), "kapas": ("Kapas", 7521),
    "bajra": ("Bajra", 2625),
    "jowar": ("Jowar", 3371),
    "groundnut": ("Moongfali", 6783), "moongfali": ("Moongfali", 6783),
    "gram": ("Chana", 5440), "chana": ("Chana", 5440),
    "lentil": ("Masoor", 6425), "masoor": ("Masoor", 6425),
    "moong": ("Moong", 8682),
    "urad": ("Urad", 7400),
    "sugarcane": ("Ganna", 340), "ganna": ("Ganna", 340),
    "sunflower": ("Surajmukhi", 7280),
}


async def get_weather(district: str, state: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            geo = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": district, "count": 1, "language": "en", "format": "json"}
            )
        if geo.status_code != 200 or not geo.json().get("results"):
            return f"{district} ka mausam abhi uplabdh nahi hai."

        loc = geo.json()["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]

        async with httpx.AsyncClient(timeout=10) as client:
            w = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat, "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                    "timezone": "Asia/Kolkata", "forecast_days": 1,
                }
            )
        if w.status_code != 200:
            return f"{district} ka mausam abhi uplabdh nahi hai."

        cur = w.json()["current"]
        daily = w.json().get("daily", {})
        temp = cur["temperature_2m"]
        humidity = cur["relative_humidity_2m"]
        wind = cur["wind_speed_10m"]
        rain = cur["precipitation"]
        desc = WMO_CODES.get(cur["weather_code"], "Mausam saaf hai")
        max_t = daily.get("temperature_2m_max", [temp])[0]
        min_t = daily.get("temperature_2m_min", [temp])[0]

        result = (
            f"{district}, {state} mein abhi {temp}°C temperature hai (Max: {max_t}°C, Min: {min_t}°C). "
            f"Mausam: {desc}. Namee: {humidity}%. Hawa: {wind} km/h. "
        )
        if rain > 0:
            result += f"Aaj {rain}mm baarish hui hai. "
        if cur["weather_code"] in [61, 63, 65, 80, 81, 82]:
            result += "Baarish ho rahi hai, khet mein kaam sambhal ke karein."
        elif temp > 40:
            result += "Bahut garmi hai, fasal ko zyada paani dein."
        elif temp < 10:
            result += "Thandi bahut hai, pala padne ka darr hai, fasal ko bachayein."
        else:
            result += "Mausam kheti ke liye theek hai."
        return result

    except Exception:
        return f"{district} ka mausam abhi uplabdh nahi hai."


async def get_mandi_price(crop: str, district: str) -> str:
    key = crop.lower().strip()
    info = MSP.get(key)
    if not info:
        for k, v in MSP.items():
            if k in key or key in k:
                info = v
                break

    if not info:
        return (
            f"{crop} ka bhav abhi uplabdh nahi hai. "
            f"Agmarknet (agmarknet.nic.in) ya nazdiki mandi par check karein."
        )

    name, msp_price = info
    market_low = int(msp_price * 1.02)
    market_high = int(msp_price * 1.12)

    return (
        f"{district} mein {name} ke bhav:\n"
        f"  Sarkari MSP (2024-25): Rs {msp_price} per quintal\n"
        f"  Mandi market bhav (anumaan): Rs {market_low} - {market_high} per quintal\n"
        f"  Sahi bhav ke liye Agmarknet (agmarknet.nic.in) check karein.\n"
        f"  Yaad rakhein: MSP se kam mein mat bechein, yeh aapka adhikar hai."
    )
