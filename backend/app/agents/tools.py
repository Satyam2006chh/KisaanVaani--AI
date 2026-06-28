import asyncio
import httpx
import logging

logger = logging.getLogger(__name__)

WMO_CODES = {
    0: "Saaf aasman", 1: "Zyaadatar saaf", 2: "Aansik badal", 3: "Badal chhaye hain",
    45: "Kohra", 48: "Barf wala kohra",
    51: "Halki boondi", 53: "Boondi", 55: "Tej boondi",
    61: "Halki baarish", 63: "Baarish", 65: "Tej baarish",
    71: "Halki barf", 73: "Barf", 75: "Tej barf",
    80: "Halki bauchhar", 81: "Bauchhar", 82: "Tej bauchhar",
    95: "Aandhi toofan", 99: "Toofan aur ole",
}



async def get_weather(district: str, state: str) -> str:
    try:
        # Geocode using district name
        async with httpx.AsyncClient(timeout=10) as client:
            geo = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": district, "count": 10, "language": "en", "format": "json"}
            )
        if geo.status_code != 200 or not geo.json().get("results"):
            return f"{district} ka mausam abhi uplabdh nahi hai."

        results = geo.json()["results"]
        
        # Look for a match in the correct state
        selected_loc = None
        for res in results:
            admin1 = res.get("admin1") or ""
            if state.lower() in admin1.lower() or admin1.lower() in state.lower():
                selected_loc = res
                break
        
        # If no state match found, fallback to the first result in India
        if not selected_loc:
            for res in results:
                if (res.get("country") or "").lower() == "india":
                    selected_loc = res
                    break
                    
        # Otherwise fallback to the very first result
        if not selected_loc:
            selected_loc = results[0]

        actual_lat, actual_lon = selected_loc["latitude"], selected_loc["longitude"]
        loc_label = f"{selected_loc.get('name')}, {selected_loc.get('admin1') or state}"

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

async def get_live_mandi_price_scraper(crop: str, district: str, state: str) -> str:
    """Uses Firecrawl to scrape the absolute latest live market price from the web."""
    from app.config import settings
    from datetime import date
    if not settings.firecrawl_api_key or "your_" in settings.firecrawl_api_key:
        return ""
    
    headers = {
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
        "Content-Type": "application/json",
    }
    
    today_str = date.today().strftime("%d %B %Y")
    
    def _fetch_live():
        with httpx.Client(timeout=12) as client:
            r = client.post(
                "https://api.firecrawl.dev/v1/search",
                headers=headers,
                json={
                    "query": f"latest mandi bhav {crop} in {district} {state} today mandibhav commodityonline",
                    "limit": 3,
                },
            )
            if r.status_code == 200:
                payload = r.json()
                items = payload.get("data") or payload.get("results") or []
                if items:
                    results_text = []
                    for item in items:
                        title = item.get("title") or ""
                        desc = item.get("description") or ""
                        if title or desc:
                            results_text.append(f"- {title}: {desc}")
                    
                    if results_text:
                        combined = "\n".join(results_text)
                        return f"\n\n**🌐 Live Internet Market Scraper (Real-Time):**\n{combined}"
        return ""
    
    try:
        return await asyncio.to_thread(_fetch_live)
    except Exception as e:
        logger.warning(f"Live Scraper Error: {e}")
        return ""

async def get_mandi_price(crop: str, district: str, state: str) -> str:
    """Gets real-time mandi prices using a HYBRID approach: Agmarknet + AI Web Scraping"""
    from app.config import settings
    
    official_data = ""
    # Try fetching official data from data.gov.in
    if settings.datagov_api_key and "your_" not in settings.datagov_api_key:
        try:
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
            
            if r.status_code == 200:
                data = r.json().get("records", [])
                if data:
                    crop_data = [d for d in data if crop.lower() in d.get("commodity", "").lower()]
                    if not crop_data:
                        crop_data = [data[0]] 
                    d = crop_data[0]
                    official_data = (
                        f"**Sarkari Mandi Rate (Agmarknet):**\n"
                        f"Mandi: {d['market']}, {d['district']}\n"
                        f"Fasal: {d['commodity']}\n"
                        f"Price: Rs {d['min_price']} - Rs {d['max_price']} (Average: Rs {d['modal_price']})\n"
                        f"Date: {d['arrival_date']}"
                    )
        except Exception as e:
            logger.error(f"Agmarknet Error: {e}")

    # Fire up the Live Scraper (Free Real-Time)
    live_data = await get_live_mandi_price_scraper(crop, district, state)
    
    if official_data or live_data:
        response = official_data + live_data
        return response.strip()
    
    return (
        f"Adarniya kisaan bhaai, abhi {district} mein {crop} ke live rates fetch karne mein dikkat aa rahi hai. "
        "Kripya thodi der baad dobara koshish karein."
    )


async def scrape_agricultural_news(query: str) -> str:
    """Uses Firecrawl to get the latest agricultural news or scheme details."""
    if not settings.firecrawl_api_key or "your_" in settings.firecrawl_api_key:
        return "System configuration missing. News fetch nahi ho sakta."
    headers = {
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
        "Content-Type": "application/json",
    }

    def _fetch_news() -> str:
        with httpx.Client(timeout=12) as client:
            r = client.post(
                "https://api.firecrawl.dev/v1/search",
                headers=headers,
                json={
                    "query": f"{query} latest agriculture news hindi krishi jagran aaj tak",
                    "limit": 4,
                },
            )

            if r.status_code == 200:
                payload = r.json()
                items = payload.get("data") or payload.get("results") or []
                if items:
                    lines = []
                    for item in items[:3]:
                        title = item.get("title") or item.get("metadata", {}).get("title") or "Untitled"
                        url = item.get("url") or item.get("sourceURL") or ""
                        desc = item.get("description") or ""
                        desc = str(desc).strip().replace("\n", " ")
                        lines.append(f"- {title}: {desc[:220]}{'...' if len(desc) > 220 else ''} {url}".strip())
                    return "Latest agriculture web results:\n" + "\n".join(lines)

            return "Internet server error. News fetch nahi ho pa raha."

    try:
        return await asyncio.to_thread(_fetch_news)
    except Exception as e:
        logger.warning(f"Internet request failed: {repr(e)}")
        return "Internet se news fetch karne mein samasya aa rahi hai."


