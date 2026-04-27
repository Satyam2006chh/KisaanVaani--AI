"""Show all users in Supabase to find Pratham's exact record"""
import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from app.db.supabase import get_supabase

sb = get_supabase()
users = sb.table("users").select("phone, name, district, state, language").order("created_at", desc=True).limit(20).execute()
print(f"\n{'='*60}")
print(f"ALL USERS IN DB ({len(users.data)} shown):")
print(f"{'='*60}")
for u in users.data:
    print(f"  phone={u.get('phone'):<15} name={u.get('name'):<15} district={u.get('district')}")
