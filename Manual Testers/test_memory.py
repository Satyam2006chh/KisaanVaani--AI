import asyncio
import os
import sys
import uuid
from dotenv import load_dotenv

# Add backend to path
sys.path.append('backend')

from app.agents.graph import agent
from app.db.supabase import get_supabase
from app.routers.history import save_message

load_dotenv('backend/.env')

async def test_memory():
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    farmer_id = "9517830697" # Yajatt VK Puri
    
    print(f"--- STARTING MULTI-TURN TEST (Session: {session_id}) ---")
    
    # 1. First Turn: Vision Analysis
    print("\nTURN 1: Uploading Image & Asking for Diagnosis...")
    img_path = 'Manual Testers/test_image.jpg'
    import base64
    with open(img_path, 'rb') as f:
        img_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"

    state_1 = {
        "messages":     [{"role": "user", "content": "Bimari batao?"}],
        "farmer_id":    farmer_id,
        "farmer_name":  "Yajatt VK Puri",
        "language":     "hi-IN",
        "city":         "Rewari",
        "district":     "Rewari",
        "state_name":   "Haryana",
        "intent":       "",
        "tool_result":  "",
        "final_answer": "",
        "image_data":   img_b64,
    }
    
    res_1 = await agent.ainvoke(state_1)
    ans_1 = res_1.get("final_answer", "")
    print(f"\n--- FULL SCIENTIST REPORT (Turn 1) ---\n{ans_1}\n")
    
    # Save to Supabase (Mocking agent.py behavior)
    await save_message(farmer_id, session_id, "user", "Bimari batao?")
    await save_message(farmer_id, session_id, "assistant", ans_1)
    
    # 2. Second Turn: Follow-up (No Image)
    print("\nTURN 2: Asking Follow-up (Cheapest treatment?)...")
    
    # Load history like agent.py does
    sb = get_supabase()
    hist_res = sb.table("messages").select("role", "content")\
        .eq("farmer_id", farmer_id)\
        .eq("session_id", session_id)\
        .order("timestamp", desc=True).limit(10).execute()
    
    history_msgs = []
    for m in reversed(hist_res.data or []):
        history_msgs.append({"role": m["role"], "content": m["content"]})
        
    state_2 = {
        "messages":     history_msgs + [{"role": "user", "content": "Ise theek karne ka sabse sasta tarika kya hai?"}],
        "farmer_id":    farmer_id,
        "farmer_name":  "Yajatt VK Puri",
        "language":     "hi-IN",
        "city":         "Rewari",
        "district":     "Rewari",
        "state_name":   "Haryana",
        "intent":       "",
        "tool_result":  "",
        "final_answer": "",
        "image_data":   None,
    }
    
    res_2 = await agent.ainvoke(state_2)
    ans_2 = res_2.get("final_answer", "")
    print(f"AI Answer 2: {ans_2}")
    
    # Validating Memory: It should mention the disease name or the specific treatment from context
    if "Early Blight" in ans_2 or "Alternaria" in ans_2 or "Mancozeb" in ans_2 or "Neem" in ans_2:
         print("\n✅ SUCCESS: Context Awareness Verified!")
    else:
         print("\n❌ FAILED: AI did not show context memory.")

if __name__ == "__main__":
    asyncio.run(test_memory())
