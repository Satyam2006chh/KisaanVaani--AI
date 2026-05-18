import httpx
import sys

# Ensure stdout handles UTF-8 correctly on Windows
sys.stdout.reconfigure(encoding='utf-8')

# We send a general agricultural query to test the OpenRouter model cascade on Render
payload = {
    "farmer_id": "guest_satyam",
    "session_id": "test_chat_session_789",
    "message": "Karnal me dhaan (rice) lagane ka sahi samay kya hai?",
    "english_message": "What is the correct time to sow rice in Karnal?",
    "language": "hi-IN",
    "image": None
}

try:
    print("Querying live OpenRouter Model Cascade via Render backend...")
    r = httpx.post("https://kisaanvaani-ai-1.onrender.com/api/agent/chat", json=payload, timeout=60)
    print(f"Status Code: {r.status_code}")
    print("\n--- Live OpenRouter Response ---")
    data = r.json()
    print(data.get("response", "No response content found."))
except Exception as e:
    print(f"Failed to query live backend: {e}")
