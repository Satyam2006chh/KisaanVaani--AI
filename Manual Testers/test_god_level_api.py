import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.agents.tools import get_weather, get_mandi_price
from app.agents.graph import weather_node, mandi_node, AgentState

async def test_weather_gps():
    print("\n--- TESTING GOD-LEVEL WEATHER (COORDINATES) ---")
    # Coordinates for Rewari, Haryana
    lat, lon = 28.19, 76.62
    print(f"Fetching weather for Lat: {lat}, Lon: {lon}...")
    
    res = await get_weather("Rewari", "Haryana", lat, lon)
    print(f"RESULT:\n{res}")
    
    if "POP" in res or "sambhavna" in res.lower():
        print("SUCCESS: Probability of Precipitation detected!")
    else:
        print("FAIL: POP data missing.")

async def test_mandi_intelligence():
    print("\n--- TESTING MANDI INTELLIGENCE (COMPARISON) ---")
    crop = "Mustard"
    dist = "Rewari"
    st = "Haryana"
    
    print(f"Fetching rates for {crop} in {dist}, {st}...")
    res = await get_mandi_price(crop, dist, st)
    print(f"RESULT:\n{res}")
    
    if "Minimum" in res and "Maximum" in res:
        print("SUCCESS: Detailed Mandi rates fetched!")
    else:
        print("FAIL: Mandi rates missing.")

async def run_all_tests():
    print("STARTING: KisaanVaani 2.0 - API HEALTH CHECK")
    await test_weather_gps()
    await test_mandi_intelligence()
    print("\nALL TESTS COMPLETED!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
