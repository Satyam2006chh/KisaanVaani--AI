import requests
import json

print("Testing Firecrawl...")
try:
    fc_key = 'fc-04e097376d8f46bab5d1ebe44eb748d1'
    r = requests.post(
        'https://api.firecrawl.dev/v1/search',
        headers={'Authorization': f'Bearer {fc_key}', 'Content-Type': 'application/json'},
        json={'query': 'agriculture news', 'limit': 1},
        timeout=10
    )
    print('Firecrawl status:', r.status_code)
    print('Firecrawl response:', r.text[:200])
except Exception as e:
    print('Firecrawl exception:', e)

print("\nTesting Agmarknet...")
try:
    datagov = '579b464db66ec23bdd000001625443631b0c44fe4bcd475a1b3063e3'
    url = f'https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070?api-key={datagov}&format=json&limit=1'
    r2 = requests.get(url, timeout=10)
    print('Agmarknet status:', r2.status_code)
    print('Agmarknet response:', r2.text[:200])
except Exception as e:
    print('Agmarknet exception:', e)
