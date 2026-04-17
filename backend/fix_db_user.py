import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("backend/.env")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
sb = create_client(url, key)

def fix_user():
    # Attempt to fix the test user
    phone = "9876543210"
    data = {
        "name": "Test Kisaan",
        "district": "Hoshangabad",
        "state": "Madhya Pradesh",
        "language": "hi-IN"
    }
    
    # Check if exists
    res = sb.table("users").select("*").eq("phone", phone).execute()
    if res.data:
        print(f"Updating user {phone}...")
        sb.table("users").update(data).eq("phone", phone).execute()
    else:
        print(f"Creating user {phone}...")
        data["phone"] = phone
        sb.table("users").insert(data).execute()
    print("Done!")

if __name__ == "__main__":
    fix_user()
