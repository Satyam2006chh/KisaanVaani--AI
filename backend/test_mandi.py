import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()
from app.agents.tools import get_mandi_price

async def main():
    crop = "Wheat"
    district = "Jaipur"
    state = "Rajasthan"
    
    result = await get_mandi_price(crop, district, state)
    
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("=== FINAL RESPONSE FROM TOOL ===\n")
        f.write(result)
        f.write("\n================================")

if __name__ == "__main__":
    asyncio.run(main())
