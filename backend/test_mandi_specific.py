import asyncio
import os
import sys

# Add the backend directory to sys.path so we can import app
sys.path.append(os.getcwd())

from app.agents.graph import agent
from app.models.schemas import ChatRequest

async def test_specific_mandi():
    # Mocking the state for Anita from Saharanpur asking about Karnal
    initial_state = {
        "messages": [{"role": "user", "content": "Ludhiana mandi mein gehu ka bhav kya hai?"}],
        "farmer_id": "8445799110",
        "farmer_name": "Anita",
        "language": "hi-IN",
        "city": "Saharanpur",
        "district": "Saharanpur",
        "state_name": "Uttar Pradesh",
        "intent": "mandi", # Force mandi intent for test
        "tool_result": "",
        "final_answer": "",
        "image_data": None,
        "original_message": "Ludhiana mandi mein gehu ka bhav kya hai?"
    }

    print(f"Testing Query: {initial_state['original_message']}")
    print("Wait, fetching real data from API...")

    try:
        # We need to set the intent correctly as intent_router would do
        # For this test, we'll just run it through the agent
        result = await agent.ainvoke(initial_state)
        print("\n" + "="*50)
        print("AI RESPONSE:")
        print("="*50)
        print(result.get("final_answer"))
        print("="*50)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_specific_mandi())
