import asyncio
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.agents.graph import agent

async def manual_agent_test():
    # TEST CASE: Satyam from Patiala asking about weather and wheat
    initial_state = {
        "messages": [{"role": "user", "content": "Satyam ji, Patiala mein aaj ka mausam aur gehu ka bhav bataiye."}],
        "farmer_id": "9999999999",
        "farmer_name": "Satyam",
        "language": "hi-IN",
        "city": "Patiala",
        "district": "Patiala",
        "state_name": "Punjab",
        "intent": "", # Agent will decide intent
        "tool_result": "",
        "final_answer": "",
        "image_data": None,
        "original_message": "Satyam ji, Patiala mein aaj ka mausam aur gehu ka bhav bataiye."
    }

    print("--- MANUAL AGENT TEST START ---")
    print(f"User Message: {initial_state['original_message']}")
    print("Agent is thinking and fetching data from multiple tools...")

    try:
        # Run the agent
        result = await agent.ainvoke(initial_state)
        
        print("\n" + "🌟" * 20)
        print("AGENT'S FINAL RESPONSE:")
        print("🌟" * 20)
        print(result.get("final_answer"))
        print("🌟" * 20)
        
        print(f"\nDetected Intent: {result.get('intent')}")
        
    except Exception as e:
        print(f"CRITICAL ERROR DURING TEST: {e}")

if __name__ == "__main__":
    asyncio.run(manual_agent_test())
