"""
Diagnostic: Check Supabase for logged-in user's actual name
and find if 'Satyam' is polluting old messages.
"""
import asyncio, sys, os
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from app.db.supabase import get_supabase

def check_user(phone: str):
    sb = get_supabase()

    # 1. Check user profile
    res = sb.table("users").select("*").eq("phone", phone).execute()
    if res.data:
        u = res.data[0]
        print(f"\n✅ USER PROFILE from Supabase:")
        print(f"   name     : {u.get('name')}")
        print(f"   phone    : {u.get('phone')}")
        print(f"   district : {u.get('district')}")
        print(f"   state    : {u.get('state')}")
        print(f"   language : {u.get('language')}")
    else:
        print(f"\n❌ No user found for phone: {phone}")
        return

    # 2. Check recent messages — look for wrong names
    msgs = sb.table("messages").select("*").eq("farmer_id", phone)\
        .order("timestamp", desc=True).limit(20).execute()

    print(f"\n📜 LAST 20 MESSAGES for {phone}:")
    for m in msgs.data or []:
        content_preview = (m.get("content") or "")[:80].replace("\n", " ")
        print(f"   [{m.get('role')}] {content_preview}")

    # 3. Count messages with wrong names
    print("\n🔍 Name pollution check:")
    for wrong_name in ["Satyam", "satyam", "Test", "test"]:
        found = [m for m in (msgs.data or []) if wrong_name in (m.get("content") or "")]
        if found:
            print(f"   ❌ Found '{wrong_name}' in {len(found)} messages!")
        else:
            print(f"   ✅ No '{wrong_name}' found in recent messages")

if __name__ == "__main__":
    phone = input("Enter phone number of logged-in user (Pratham): ").strip()
    check_user(phone)
