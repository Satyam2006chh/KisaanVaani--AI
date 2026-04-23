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


async def get_weather(district: str, state: str, lat: float = None, lon: float = None) -> str:
    try:
        # Check if coordinates are provided directly from user GPS
        if lat is not None and lon is not None:
            actual_lat, actual_lon = lat, lon
            loc_label = f"Aapke khet (Lat: {lat}, Lon: {lon})"
        else:
            # Fallback to district geocoding
            async with httpx.AsyncClient(timeout=10) as client:
                geo = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": district, "count": 1, "language": "en", "format": "json"}
                )
            if geo.status_code != 200 or not geo.json().get("results"):
                return f"{district} ka mausam abhi uplabdh nahi hai."

            loc = geo.json()["results"][0]
            actual_lat, actual_lon = loc["latitude"], loc["longitude"]
            loc_label = f"{district}, {state}"

        # Fetch High-Precision Forecast
        async with httpx.AsyncClient(timeout=10) as client:
            w = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": actual_lat, "longitude": actual_lon,
                    "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
                    "timezone": "Asia/Kolkata", "forecast_days": 1,
                }
            )
        if w.status_code != 200:
            return f"{loc_label} ka mausam abhi uplabdh nahi hai."

        cur = w.json()["current"]
        daily = w.json().get("daily", {})
        temp = cur["temperature_2m"]
        humidity = cur["relative_humidity_2m"]
        wind = cur["wind_speed_10m"]
        rain = cur["precipitation"]
        # PREDICTIVE RAIN PROBABILITY (POP)
        rain_prob = daily.get("precipitation_probability_max", [0])[0]
        
        desc = WMO_CODES.get(cur["weather_code"], "Mausam saaf hai")
        max_t = daily.get("temperature_2m_max", [temp])[0]
        min_t = daily.get("temperature_2m_min", [temp])[0]

        result = (
            f"**Data for {loc_label}:**\n"
            f"Abhi temperature {temp}°C hai (Dopahar ka max {max_t}°C, Raat ka min {min_t}°C).\n"
            f"Sthiti: {desc}. Namee (Humidity): {humidity}%. Hawa ki gati: {wind} km/h.\n"
            f"Baarish ki sambhavna (POP): {rain_prob}%.\n"
        )
        
        # EXPERT ADVICE BASED ON DATA
        if rain_prob > 70:
            result += "🚨 ALERT: Baarish ke 70% se zyada chances hain. Kripya dhaan ya mandi mein rakhi fasal ko turant dhak dein (Cover your crops)."
        elif rain_prob > 30:
            result += "Badal chhaye reh sakte hain, halki bauchhaar ki umeed hai."
        
        if temp > 42:
            result += " 🔥 Bahut garam hawaayein chalne ka darr hai, fasal ki light sinchai (irrigation) dopahar se pehle zaroori hai."
        elif temp < 8:
            result += " ❄️ Thandi ka pekhop hai, pala (frost) padne ka darr hai. Dhuan karke ya halka pani dekar fasal bachayein."
            
        return result

    except Exception as e:
        logger.error(f"Weather Tool Error: {e}")
        return f"{district} ka mausam fetch karne mein samasya aa rahi hai."


from app.config import settings

async def get_mandi_price(crop: str, district: str, state: str) -> str:
    """Gets real-time mandi prices from data.gov.in (Agmarknet)"""
    if not settings.datagov_api_key or "your_" in settings.datagov_api_key:
        # Fallback to MSP logic if no API key
        key = crop.lower().strip()
        info = MSP.get(key)
        if not info:
            for k, v in MSP.items():
                if k in key or key in k:
                    info = v
                    break
        if not info:
            return (
                f"Kshama karein, {crop} ka bhav abhi mere paas nahi mil pa raha hai. "
                "Par fikar na karein! Aap mujhse kisi aur fasal ke baare mein pooch sakte hain "
                "ya thodi der baad phir se koshish kar sakte hain. Main aapki madad hamesha karunga!"
            )
        
        name, msp_price = info
        market_low = int(msp_price * 1.02)
        market_high = int(msp_price * 1.12)
        return (
            f"[OFFLINE DATA] {district} mein {name} ke bhav:\n"
            f"  MSP: Rs {msp_price}/quintal\n"
            f"  Anumaanit Mandi bhav: Rs {market_low} - {market_high}/quintal\n"
            f"  (Kripya data.gov.in API key set karein real-time rates ke liye)"
        )

    try:
        # Correct Resource ID for Mandi Prices
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        params = {
            "api-key": settings.datagov_api_key,
            "format": "json",
            "limit": 5,
            "filters[state]": state,
            "filters[district]": district,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params)
        
        if r.status_code != 200:
            return f"Mandi rates fetch karne mein error. Agmarknet par check karein."
        
        data = r.json().get("records", [])
        if not data:
            return (
                f"Namaste! {district} ki mandi mein abhi {crop} ka naya rate update nahi hua hai. "
                "Aksar bazaar band hone pe ya seasonal badlav ki wajah se aisa hota hai. "
                "Aap mujhse kisi aur mandi ya fasal ke baare mein pooch sakte hain, main turant check karunga!"
            )
        
        # Filter for the specific crop
        crop_data = [d for d in data if crop.lower() in d.get("commodity", "").lower()]
        if not crop_data:
            crop_data = [data[0]] # Just show the first available arrival if crop not found
        
        d = crop_data[0]
        res = (
            f"Aaj {d['market']} mandi ({d['district']}) mein {d['commodity']} ka rate:\n"
            f"  Minimum: Rs {d['min_price']}\n"
            f"  Maximum: Rs {d['max_price']}\n"
            f"  Modal (Average): Rs {d['modal_price']}\n"
            f"  Update date: {d['arrival_date']}"
        )
        return res
    except Exception as e:
        return f"Mandi rate error: {str(e)}"


import math

# REGIONAL MANDI DATABASE (Lat, Lon, Name)
# This will be expanded/queried from Agmarknet, but for proximity matching:
MANDI_HUBS = [
    {"name": "Fatehgarh Sahib", "lat": 30.64, "lon": 76.39, "state": "Punjab"},
    {"name": "Ambala City", "lat": 30.37, "lon": 76.77, "state": "Haryana"},
    {"name": "Saharanpur", "lat": 29.96, "lon": 77.55, "state": "Uttar Pradesh"},
    {"name": "Rajpura", "lat": 30.48, "lon": 76.59, "state": "Punjab"},
    {"name": "Sirhind", "lat": 30.62, "lon": 76.40, "state": "Punjab"},
    {"name": "Karnal", "lat": 29.68, "lon": 76.99, "state": "Haryana"},
    {"name": "Rohtak", "lat": 28.89, "lon": 76.60, "state": "Haryana"},
    {"name": "Batala", "lat": 31.81, "lon": 75.20, "state": "Punjab"},
]

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

async def get_nearest_mandis(lat: float, lon: float):
    """Finds top 3 nearest mandis from the hub list and fetches rates if possible."""
    nearby = []
    for m in MANDI_HUBS:
        dist = calculate_distance(lat, lon, m["lat"], m["lon"])
        if dist < 100: # Within 100km
            m_copy = m.copy()
            m_copy["distance"] = round(dist, 1)
            nearby.append(m_copy)
    
    # Sort by distance
    nearby.sort(key=lambda x: x["distance"])
    return nearby[:3]
