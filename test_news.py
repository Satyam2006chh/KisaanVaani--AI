import asyncio
import sys
import os
sys.path.append(os.getcwd())

from app.agents.graph import agent

async def main():
    state = {
        "messages": [{"role": "user", "content": "kheti badi se judi aaj ki taza khabar sunao"}],
        "farmer_id": "test_id",
        "farmer_name": "Raj yadav",
        "language": "hi-IN",
        "city": "Rajpura",
        "district": "Patiala",
        "state_name": "Punjab",
        "intent": "",
        "tool_result": "",
        "final_answer": "",
        "image_data": "",
        "original_message": "kheti badi se judi aaj ki taza khabar sunao"
    }
    
    print("Running graph...")
    result = await agent.ainvoke(state)
    print("\n\n--- FINAL ANSWER ---")
    print(result["final_answer"])
    print("--------------------")

if __name__ == "__main__":
    asyncio.run(main())
