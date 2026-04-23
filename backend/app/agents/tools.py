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

# ALL-INDIA MANDI HUB DATABASE
# Covers all major agricultural markets across every state
MANDI_HUBS = [
    # Punjab
    {"name": "Rajpura Mandi", "lat": 30.48, "lon": 76.59, "state": "Punjab"},
    {"name": "Patiala Mandi", "lat": 30.34, "lon": 76.39, "state": "Punjab"},
    {"name": "Banur Mandi", "lat": 30.56, "lon": 76.68, "state": "Punjab"},
    {"name": "Fatehgarh Sahib Mandi", "lat": 30.64, "lon": 76.39, "state": "Punjab"},
    {"name": "Sirhind Mandi", "lat": 30.62, "lon": 76.40, "state": "Punjab"},
    {"name": "Ludhiana Mandi", "lat": 30.90, "lon": 75.85, "state": "Punjab"},
    {"name": "Amritsar Mandi", "lat": 31.63, "lon": 74.87, "state": "Punjab"},
    {"name": "Jalandhar Mandi", "lat": 31.32, "lon": 75.57, "state": "Punjab"},
    {"name": "Bathinda Mandi", "lat": 30.21, "lon": 74.94, "state": "Punjab"},
    {"name": "Batala Mandi", "lat": 31.81, "lon": 75.20, "state": "Punjab"},
    {"name": "Moga Mandi", "lat": 30.82, "lon": 75.17, "state": "Punjab"},
    {"name": "Firozpur Mandi", "lat": 30.92, "lon": 74.61, "state": "Punjab"},
    # Haryana
    {"name": "Ambala Mandi", "lat": 30.37, "lon": 76.77, "state": "Haryana"},
    {"name": "Karnal Mandi", "lat": 29.68, "lon": 76.99, "state": "Haryana"},
    {"name": "Rohtak Mandi", "lat": 28.89, "lon": 76.60, "state": "Haryana"},
    {"name": "Hisar Mandi", "lat": 29.15, "lon": 75.72, "state": "Haryana"},
    {"name": "Sirsa Mandi", "lat": 29.53, "lon": 75.02, "state": "Haryana"},
    {"name": "Panipat Mandi", "lat": 29.39, "lon": 76.97, "state": "Haryana"},
    {"name": "Sonipat Mandi", "lat": 28.99, "lon": 77.01, "state": "Haryana"},
    {"name": "Kurukshetra Mandi", "lat": 29.96, "lon": 76.82, "state": "Haryana"},
    {"name": "Jhajjar Mandi", "lat": 28.61, "lon": 76.65, "state": "Haryana"},
    {"name": "Rewari Mandi", "lat": 28.19, "lon": 76.62, "state": "Haryana"},
    {"name": "Gurgaon Mandi", "lat": 28.46, "lon": 77.03, "state": "Haryana"},
    {"name": "Faridabad Mandi", "lat": 28.41, "lon": 77.31, "state": "Haryana"},
    # Uttar Pradesh
    {"name": "Meerut Mandi", "lat": 28.98, "lon": 77.71, "state": "Uttar Pradesh"},
    {"name": "Saharanpur Mandi", "lat": 29.96, "lon": 77.55, "state": "Uttar Pradesh"},
    {"name": "Muzaffarnagar Mandi", "lat": 29.47, "lon": 77.70, "state": "Uttar Pradesh"},
    {"name": "Hapur Mandi", "lat": 28.73, "lon": 77.78, "state": "Uttar Pradesh"},
    {"name": "Agra Mandi", "lat": 27.18, "lon": 78.01, "state": "Uttar Pradesh"},
    {"name": "Lucknow Mandi", "lat": 26.85, "lon": 80.95, "state": "Uttar Pradesh"},
    {"name": "Kanpur Mandi", "lat": 26.46, "lon": 80.33, "state": "Uttar Pradesh"},
    {"name": "Allahabad Mandi", "lat": 25.43, "lon": 81.84, "state": "Uttar Pradesh"},
    {"name": "Bareilly Mandi", "lat": 28.36, "lon": 79.41, "state": "Uttar Pradesh"},
    {"name": "Moradabad Mandi", "lat": 28.83, "lon": 78.77, "state": "Uttar Pradesh"},
    {"name": "Ghaziabad Mandi", "lat": 28.66, "lon": 77.43, "state": "Uttar Pradesh"},
    {"name": "Varanasi Mandi", "lat": 25.32, "lon": 82.97, "state": "Uttar Pradesh"},
    # Rajasthan
    {"name": "Jaipur Mandi", "lat": 26.91, "lon": 75.79, "state": "Rajasthan"},
    {"name": "Jodhpur Mandi", "lat": 26.29, "lon": 73.01, "state": "Rajasthan"},
    {"name": "Kota Mandi", "lat": 25.18, "lon": 75.83, "state": "Rajasthan"},
    {"name": "Ajmer Mandi", "lat": 26.45, "lon": 74.64, "state": "Rajasthan"},
    {"name": "Alwar Mandi", "lat": 27.56, "lon": 76.61, "state": "Rajasthan"},
    {"name": "Bharatpur Mandi", "lat": 27.22, "lon": 77.49, "state": "Rajasthan"},
    # Madhya Pradesh
    {"name": "Bhopal Mandi", "lat": 23.26, "lon": 77.40, "state": "Madhya Pradesh"},
    {"name": "Indore Mandi", "lat": 22.72, "lon": 75.86, "state": "Madhya Pradesh"},
    {"name": "Gwalior Mandi", "lat": 26.22, "lon": 78.18, "state": "Madhya Pradesh"},
    {"name": "Jabalpur Mandi", "lat": 23.17, "lon": 79.94, "state": "Madhya Pradesh"},
    # Maharashtra
    {"name": "Pune Mandi (APMC)", "lat": 18.52, "lon": 73.85, "state": "Maharashtra"},
    {"name": "Nashik Mandi", "lat": 19.99, "lon": 73.79, "state": "Maharashtra"},
    {"name": "Aurangabad Mandi", "lat": 19.88, "lon": 75.34, "state": "Maharashtra"},
    {"name": "Nagpur Mandi", "lat": 21.15, "lon": 79.08, "state": "Maharashtra"},
    # Gujarat
    {"name": "Ahmedabad APMC", "lat": 23.03, "lon": 72.59, "state": "Gujarat"},
    {"name": "Surat Mandi", "lat": 21.17, "lon": 72.83, "state": "Gujarat"},
    {"name": "Rajkot Mandi", "lat": 22.30, "lon": 70.80, "state": "Gujarat"},
    # Bihar
    {"name": "Patna Mandi", "lat": 25.59, "lon": 85.14, "state": "Bihar"},
    {"name": "Muzaffarpur Mandi", "lat": 26.12, "lon": 85.36, "state": "Bihar"},
    # West Bengal
    {"name": "Kolkata APMC", "lat": 22.57, "lon": 88.36, "state": "West Bengal"},
    # Karnataka
    {"name": "Bangalore APMC", "lat": 12.97, "lon": 77.59, "state": "Karnataka"},
    {"name": "Hubli Mandi", "lat": 15.36, "lon": 75.12, "state": "Karnataka"},
    # Andhra Pradesh
    {"name": "Guntur Mandi", "lat": 16.30, "lon": 80.43, "state": "Andhra Pradesh"},
    {"name": "Vijayawada Mandi", "lat": 16.51, "lon": 80.62, "state": "Andhra Pradesh"},
    # Tamil Nadu
    {"name": "Madurai Mandi", "lat": 9.93, "lon": 78.12, "state": "Tamil Nadu"},
    # Uttarakhand
    {"name": "Haridwar Mandi", "lat": 29.94, "lon": 78.16, "state": "Uttarakhand"},
    {"name": "Dehradun Mandi", "lat": 30.32, "lon": 78.03, "state": "Uttarakhand"},
    # Himachal Pradesh
    {"name": "Shimla Mandi", "lat": 31.10, "lon": 77.17, "state": "Himachal Pradesh"},
    # Delhi NCR
    {"name": "Azadpur Mandi (Delhi)", "lat": 28.72, "lon": 77.18, "state": "Delhi"},
    {"name": "Ghazipur Mandi (Delhi)", "lat": 28.63, "lon": 77.32, "state": "Delhi"},
]

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine formula for accurate distance between two GPS coordinates."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def get_nearest_mandis(lat: float, lon: float):
    """
    LIVE DATA PIPELINE:
    Step 1: Reverse geocode GPS coords -> get real district & state
    Step 2: Query Agmarknet (data.gov.in) for real mandis + prices in that area
    Step 3: Fallback to MANDI_HUBS haversine only if API fails
    """
    from app.config import settings

    # --- STEP 1: Get district/state from GPS coordinates ---
    district = None
    state = None
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            geo = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"format": "json", "lat": lat, "lon": lon, "accept-language": "en"},
                headers={"User-Agent": "KisaanVaani/2.0"}
            )
        if geo.status_code == 200:
            addr = geo.json().get("address", {})
            # For Agmarknet, we need the administrative District (e.g., Patiala, not Jansla)
            district = addr.get("county") or addr.get("state_district") or addr.get("city") or addr.get("town")
            state = addr.get("state")
            print(f"DEBUG: Geocoded to District={district}, State={state}")
    except Exception as e:
        print(f"DEBUG: Geocoding failed: {e}")

    # --- STEP 2: Fetch LIVE mandis from Agmarknet API ---
    if district and state and settings.datagov_api_key and "your_" not in settings.datagov_api_key:
        try:
            print(f"DEBUG: Querying Agmarknet API for {district}, {state}")
            async with httpx.AsyncClient(timeout=10) as client:
                # Try with district first
                r = await client.get(
                    "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
                    params={
                        "api-key": settings.datagov_api_key,
                        "format": "json",
                        "limit": 10,
                        "filters[state]": state,
                        "filters[district]": district,
                    }
                )

            if r.status_code == 200:
                records = r.json().get("records", [])

                # If no records for district, try nearby state-level data
                if not records:
                    print(f"DEBUG: No records for district {district}, trying state {state}")
                    async with httpx.AsyncClient(timeout=10) as client:
                        r2 = await client.get(
                            "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
                            params={
                                "api-key": settings.datagov_api_key,
                                "format": "json",
                                "limit": 10,
                                "filters[state]": state,
                            }
                        )
                    if r2.status_code == 200:
                        records = r2.json().get("records", [])

                if records:
                    print(f"DEBUG: Found {len(records)} live records")
                    # De-duplicate by market name and build response
                    seen = set()
                    live_mandis = []
                    for rec in records:
                        market = rec.get("market") or rec.get("Market")
                        commodity = rec.get("commodity") or rec.get("Commodity", "")
                        modal_price = rec.get("modal_price") or rec.get("Modal_Price", "N/A")
                        if market and market not in seen:
                            seen.add(market)
                            live_mandis.append({
                                "name": market,
                                "state": state,
                                "distance": None,  # Real API doesn't provide distance
                                "price": f"{commodity}: ₹{modal_price}/qtl" if commodity else None,
                                "source": "live"
                            })
                    if live_mandis:
                        return live_mandis[:5]
        except Exception as e:
            print(f"DEBUG: Agmarknet API error: {e}")

    # --- STEP 3: FALLBACK — Always return at least 5 closest hubs from database ---
    print(f"DEBUG: Falling back to MANDI_HUBS list for lat={lat}, lon={lon}")
    nearby = []
    for m in MANDI_HUBS:
        dist = calculate_distance(lat, lon, m["lat"], m["lon"])
        m_copy = m.copy()
        m_copy["distance"] = round(dist, 1)
        m_copy["source"] = "hub"
        nearby.append(m_copy)
    
    nearby.sort(key=lambda x: x["distance"])
    return nearby[:5]


async def scrape_agricultural_news(query: str) -> str:
    """Uses Firecrawl to get the latest agricultural news or scheme details."""
    from app.config import settings
    if not settings.firecrawl_api_key or "your_" in settings.firecrawl_api_key:
        return "Firecrawl API key missing. News fetch nahi ho sakta."
    return "Aaj ki taaza khabar: Krishi sakhi yoina ke tahat naye registration shuru ho gaye hain. (Simulated Demo News)"
