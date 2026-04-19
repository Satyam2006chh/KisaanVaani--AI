import asyncio
import os
from dotenv import load_dotenv
import sys

# Add backend to path
sys.path.append('backend')

from app.agents.graph import agent
from app.config import settings

load_dotenv('backend/.env')

async def debug_chat():
    # Use the sample image we have
    with open('diagnosis_result.txt', 'r') as f: # Just checking the text file exists
        pass
    
    # Minimal base64 for testing
    sample_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

    initial_state = {
        "messages":     [{"role": "user", "content": "Bimari batao?"}],
        "farmer_id":    "9517830697",
        "farmer_name":  "Yajatt VK Puri",
        "language":     "hi-IN",
        "city":         "Rewari",
        "district":     "Rewari",
        "state_name":   "Haryana",
        "intent":       "",
        "tool_result":  "",
        "final_answer": "",
        "image_data":   sample_image,
    }
    
    print("\n--- DEBUGGING AGENT WITH IMAGE ---")
    try:
        result = await agent.ainvoke(initial_state)
        print("SUCCESS!")
        print(f"Intent: {result.get('intent')}")
        print(f"Final Answer: {result.get('final_answer')[:200]}...")
    except Exception as e:
        print(f"FAILED with Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_chat())
