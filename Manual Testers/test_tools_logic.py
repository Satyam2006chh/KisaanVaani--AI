import asyncio
import os
import sys

# Add the backend directory to path so we can import app
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.agents.graph import agent
from app.config import settings

async def test_tool_responses():
    scenarios = [
        {
            "name": "Weather",
            "query": "Hoshangabad mein kal ka mausam kaisa rahega?",
            "expected_tool": "weather"
        },
        {
            "name": "Mandi (Flexible District)",
            "query": "Indore ki mandi mein sarson ka kya bhav hai?",
            "expected_tool": "mandi"
        },
        {
            "name": "Mandi (Fallback Testing)",
            "query": "Kachre ka bhav batao?",
            "expected_tool": "mandi"
        },
        {
            "name": "News",
            "query": "Kisaano ke liye aaj ki taaza khabar batao.",
            "expected_tool": "news"
        },
        {
            "name": "Crop Advice",
            "query": "Main Bhopal se hoon, mujhe kaunsi fasal lagani chahiye?",
            "expected_tool": "crop_advice"
        },
        {
            "name": "General/Scheme",
            "query": "PM Kisan Samman Nidhi ke baare mein jankari dein.",
            "expected_tool": "scheme"
        }
    ]

    print("\n" + "="*50)
    print(" STARTING MANUAL TOOL TESTING")
    print("="*50 + "\n")

    for scenario in scenarios:
        print(f" TESTING: {scenario['name']}")
        print(f" QUESTION: {scenario['query']}")
        
        initial_state = {
            "messages":     [{"role": "user", "content": scenario['query']}],
            "farmer_id":    "test_id",
            "farmer_name":  "Test Kisaan",
            "language":     "hi-IN",
            "city":         "Bhopal",
            "district":     "Hoshangabad",
            "state_name":   "Madhya Pradesh",
            "intent":       "",
            "tool_result":  "",
            "final_answer": "",
        }

        try:
            result = await agent.ainvoke(initial_state)
            
            # Use safe printing for Windows console
            def safe_print(label, content):
                try:
                    print(f" {label}: {content}")
                except UnicodeEncodeError:
                    print(f" {label}: {content.encode('ascii', errors='replace').decode('ascii')}")

            safe_print("INTENT DETECTED", result.get('intent', 'N/A'))
            safe_print("TOOL OUTPUT", result.get('tool_result', 'N/A')[:300] + "...")
            safe_print("FINAL ANSWER", result.get('final_answer', 'N/A'))
            print("-" * 30)
            
        except Exception as e:
            print(f" ERROR: {str(e)}")
            print("-" * 30)

    print("\n" + "="*50)
    print(" TESTING COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(test_tool_responses())
