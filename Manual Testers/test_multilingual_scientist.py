import asyncio
import os
import sys

# Add the backend directory to path so we can import app
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Force load environment variables for testing
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.agents.graph import agent

async def test_multilingual_scientist():
    scenarios = [
        {
            "name": "Scientific Weather (Hindi)",
            "query": "Mumbai aur Pune mein kal ka mausam kaisa rahega?",
            "lang": "hi-IN",
            "city": "Mumbai"
        },
        {
            "name": "Expert Mandi (Punjabi)",
            "query": "Indore mandi mein sarson ka kya bhav hai?",
            "lang": "pa-IN",
            "city": "Indore"
        },
        {
            "name": "Agri-Scientist Advice (English)",
            "query": "Provide technical advice for soybean cultivation in July.",
            "lang": "en-IN",
            "city": "Hoshangabad"
        },
        {
            "name": "Dynamic Language Switch",
            "query": "Ab se mujhe Punjabi mein jawab do.",
            "lang": "hi-IN",
            "city": "Hoshangabad"
        },
        {
            "name": "Polite Out-of-Scope",
            "query": "Who is the Prime Minister of India?",
            "lang": "hi-IN",
            "city": "Indore"
        }
    ]

    print("\n" + "="*70)
    print(" KISAANVAANI AI: SCIENTIST & MULTILINGUAL MANUAL TEST")
    print("="*70 + "\n")

    for scenario in scenarios:
        print(f" TEST CASE: {scenario['name']}")
        print(f" QUESTION:  {scenario['query']}")
        print(f" LANG:      {scenario['lang']}")
        
        initial_state = {
            "messages":     [{"role": "user", "content": scenario['query']}],
            "farmer_id":    "manual_tester_123",
            "farmer_name":  "Satyam",
            "language":     scenario['lang'],
            "city":         scenario['city'],
            "district":     "Hoshangabad",
            "state_name":   "Madhya Pradesh",
            "intent":       "",
            "tool_result":  "",
            "final_answer": "",
        }

        try:
            result = await agent.ainvoke(initial_state)
            
            # 100% Plain ASCII print function
            def safe_print(label, content):
                try:
                    # Strip any emojis from content if they leaked from LLM
                    clean_content = content.encode('ascii', 'replace').decode('ascii')
                    print(f" {label}: {clean_content}")
                except Exception:
                    print(f" {label}: [Content contains non-ascii characters]")

            safe_print("INTENT", result.get('intent', 'N/A'))
            safe_print("LANGUAGE", result.get('language', 'N/A'))
            
            answer = result.get('final_answer', 'N/A')
            print(" RESPONSE:")
            lines = answer.split('.')
            for line in lines:
                line = line.strip()
                if line:
                    safe_print("  - ", line + ".")
            
            print("-" * 50)
            
        except Exception as e:
            print(f" ERROR: {str(e)}")
            print("-" * 50)

    print("\n" + "="*70)
    print(" MANUAL TESTING COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_multilingual_scientist())
