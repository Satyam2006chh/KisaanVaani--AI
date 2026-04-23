import asyncio
import os
import sys
import base64

# Add the backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load environment
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.agents.graph import agent

async def test_manual_image():
    # Use the test image2 from Manual Testers
    image_path = os.path.join(os.getcwd(), "Manual Testers", "test_image2.jpg")
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')

    initial_state = {
        "messages":     [{"role": "user", "content": "Analyze this crop image and tell me the disease and solution in Hindi."}],
        "farmer_id":    "manual_tester_satyam",
        "farmer_name":  "Satyam",
        "language":     "hi-IN",
        "city":         "Jansla",
        "district":     "Patiala",
        "state_name":   "Punjab",
        "intent":       "vision",
        "tool_result":  "",
        "final_answer": "",
        "image_data":   img_base64,
    }

    print("ANALYZING...")

    try:
        result = await agent.ainvoke(initial_state)
        answer = result.get('final_answer', 'No answer received.')
        
        with open("manual_test_result.txt", "w", encoding="utf-8") as f:
            f.write(answer)
        
        print("\n[SUCCESS] Diagnosis saved to manual_test_result.txt")
        
    except Exception as e:
        print(f" ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_manual_image())
