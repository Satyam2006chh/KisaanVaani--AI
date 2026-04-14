import httpx
from app.config import settings

async def get_weather(district: str, state: str) -> str:
    """Fetch weather for farmer's location using OpenWeatherMap."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": f"{district},{state},IN", "appid": settings.openweather_api_key, "units": "metric"}

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)

    if r.status_code != 200:
        return "Mausam ki jankari abhi uplabdh nahi hai."

    data = r.json()
    temp   = data["main"]["temp"]
    desc   = data["weather"][0]["description"]
    humid  = data["main"]["humidity"]

    return (
        f"{district} mein abhi {temp}°C temperature hai. "
        f"Mausam: {desc}. Namee (Humidity): {humid}%."
    )


async def get_mandi_price(crop: str, district: str) -> str:
    """Fetch mandi price from data.gov.in Agmarknet API."""
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    params = {
        "api-key": settings.data_gov_api_key,
        "format": "json",
        "filters[commodity]": crop,
        "filters[district]": district,
        "limit": 3,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)

    if r.status_code != 200 or not r.json().get("records"):
        return f"{crop} ka mandi bhav abhi uplabdh nahi hai."

    records = r.json()["records"]
    result = f"{district} mein {crop} ke taaze bhav:\n"
    for rec in records:
        result += f"• {rec.get('market', district)}: ₹{rec.get('modal_price', 'N/A')} per quintal\n"
    return result.strip()
