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


async def scrape_agricultural_news(query: str) -> str:
    """Uses Firecrawl to get the latest agricultural news or scheme details from live sites."""
    if not settings.firecrawl_api_key or "your_" in settings.firecrawl_api_key:
        return "Firecrawl API key missing. Latest news fetch nahi ho sakta."

    try:
        # We use Firecrawl Search/Crawl to find latest news
        url = "https://api.firecrawl.dev/v1/scrape"
        # For simplicity in demo, we'll scrape PIB India's agriculture section or a search
        target_url = f"https://pib.gov.in/allRel.aspx" # Example target
        
        headers = {
            "Authorization": f"Bearer {settings.firecrawl_api_key}",
            "Content-Type": "application/json"
        }
        
        # In a real scenario, we'd search first, but here we simulate a scrape of latest releases
        payload = {
            "url": target_url,
            "formats": ["markdown"],
            "onlyMainContent": True
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, json=payload, headers=headers)
        
        if r.status_code != 200:
            return "Latest news fetch karne mein samasya aa rahi hai."
        
        content = r.json().get("data", {}).get("markdown", "")
        # Return first 500 chars summarized
        return content[:800] + "..." if content else "Abhi koi naya update nahi mila."
    except Exception:
        return "News scan error. Kripya thodi der baad try karein."
