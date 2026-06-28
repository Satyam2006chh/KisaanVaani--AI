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
    import json
    from app.agents.weather_engine import analyze_weather
    
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
        
        if not selected_loc:
            for res in results:
                if (res.get("country") or "").lower() == "india":
                    selected_loc = res
                    break
                    
        if not selected_loc:
            selected_loc = results[0]

        actual_lat, actual_lon = selected_loc["latitude"], selected_loc["longitude"]

        # Fetch High-Precision Forecast with Agricultural Variables
        async with httpx.AsyncClient(timeout=10) as client:
            w = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": actual_lat, "longitude": actual_lon,
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,uv_index",
                    "hourly": "soil_temperature_0cm,soil_moisture_0_to_1cm,evapotranspiration",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
                    "timezone": "Asia/Kolkata", "forecast_days": 1,
                }
            )
        
        if w.status_code != 200:
            return f"{district} ka mausam abhi uplabdh nahi hai."
            
        raw_weather = w.json()
        
        # Process data using Weather Intelligence Engine
        insights = analyze_weather(raw_weather)
        
        # Return as JSON string so LLM can parse it easily
        return json.dumps(insights, indent=2)

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
                    "query": f"latest wholesale mandi price rate of {crop} in {district} {state} today napanta kisandeals indiamart",
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
    """Gets real-time mandi prices using AI Web Scraping (Firecrawl)"""
    live_data = await get_live_mandi_price_scraper(crop, district, state)
    
    if live_data:
        return live_data.strip()
    
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
                    "query": f"{query} agriculture news scheme update hindi (site:krishijagran.com OR site:aajtak.in OR site:news18.com OR site:kisansamadhan.com)",
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


