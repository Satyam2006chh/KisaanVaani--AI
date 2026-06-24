import asyncio
import sys
import os
sys.path.append(os.getcwd())

from app.agents.tools import get_live_mandi_price_scraper

async def main():
    print("Testing Scraper for Sarso in Saharanpur Uttar Pradesh...")
    result = await get_live_mandi_price_scraper("sarso", "Saharanpur", "Uttar Pradesh")
    print("\n\n--- SCRAPER RESULT ---")
    print(result)
    print("----------------------")

if __name__ == "__main__":
    asyncio.run(main())
