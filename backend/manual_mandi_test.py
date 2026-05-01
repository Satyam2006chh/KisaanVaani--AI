import asyncio
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.agents.graph import agent

async def manual_mandi_test():
    # TEST CASE: Dedicated Mandi check for Bhindi in Patiala
    initial_state = {
        "messages": [{"role": "user", "content": "Patiala mandi mein Bhindi ka kya rate chal raha hai?"}],
        "farmer_id": "9999999999",
        "farmer_name": "Satyam",
        "language": "hi-IN",
        "city": "Patiala",
        "district": "Patiala",
        "state_name": "Punjab",
        "intent": "", 
        "tool_result": "",
        "final_answer": "",
        "image_data": None,
        "original_message": "Patiala mandi mein Bhindi ka kya rate chal raha hai?"
    }

    print("--- DEDICATED MANDI TOOL TEST ---")
    try:
        result = await agent.ainvoke(initial_state)
        print("\n" + "💰" * 20)
        print("AGENT'S MANDI RESPONSE:")
        print("💰" * 20)
        print(result.get("final_answer"))
        print("💰" * 20)
        print(f"\nDetected Intent: {result.get('intent')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(manual_mandi_test())
