import asyncio
import httpx
import os
import sys

# Add the backend directory to path so we can import app
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.config import settings

async def debug_mandi():
    # Attempt with resource ID from user's screenshot
    resource_id = "9ef84268-d588-465a-a308-a864a43d0070"
    url = f"https://api.data.gov.in/resource/{resource_id}"
    
    params = {
        "api-key": settings.datagov_api_key,
        "format": "json",
        "limit": 5,
    }
    
    print(f"--- Mandi API Debug ---")
    print(f"URL: {url}")
    print(f"Key: {settings.datagov_api_key[:10]}...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.get(url, params=params)
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                records = data.get("records", [])
                print(f"Success! Found {len(records)} records.")
                if records:
                    print(f"Example Record: {records[0]}")
                return True
            else:
                print(f"Failed! Error: {r.text[:500]}")
                return False
        except Exception as e:
            print(f"Exception: {str(e)}")
            return False

if __name__ == "__main__":
    asyncio.run(debug_mandi())
