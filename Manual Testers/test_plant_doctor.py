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

async def test_plant_doctor():
    # Path to the generated diseased image (Update this to the actual generated filename)
    image_path = "C:\\Users\\ASUS\\.gemini\\antigravity\\brain\\cfeb0ed4-4e38-44a5-8a07-db0a2a8c6bc0\\diseased_tomato_leaf_1776546196494.png"
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')

    initial_state = {
        "messages":     [{"role": "user", "content": "Meri tamatar ki patti par ye dhabbe kya hain?"}],
        "farmer_id":    "manual_tester_123",
        "farmer_name":  "Satyam",
        "language":     "hi-IN",
        "city":         "Hoshangabad",
        "district":     "Hoshangabad",
        "state_name":   "Madhya Pradesh",
        "intent":       "vision",
        "tool_result":  "",
        "final_answer": "",
        "image_data":   img_base64,
    }

    print("\n" + "="*70)
    print(" KISAANVAANI AI: PLANT DOCTOR (VISION) TEST")
    print("="*70 + "\n")
    print(" ANALYZING IMAGE...")

    try:
        result = await agent.ainvoke(initial_state)
        answer = result.get('final_answer', 'N/A')
        
        with open("diagnosis_result.txt", "w", encoding="utf-8") as f:
            f.write(answer)
        
        print("\n[SUCCESS] Diagnosis saved to diagnosis_result.txt")
        
    except Exception as e:
        print(f" ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_plant_doctor())
