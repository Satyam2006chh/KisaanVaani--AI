"""
Clean DB: Delete ALL users and messages from Supabase.
Run this once to start fresh.
"""
import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from app.db.supabase import get_supabase

sb = get_supabase()

# Count before
users_before   = sb.table("users").select("phone", count="exact").execute()
msgs_before    = sb.table("messages").select("id", count="exact").execute()
print(f"\nBEFORE:")
print(f"  users    : {users_before.count}")
print(f"  messages : {msgs_before.count}")

confirm = input("\n⚠️  This will DELETE ALL users and messages. Type 'YES' to confirm: ").strip()
if confirm != "YES":
    print("Cancelled.")
    exit()

# Delete all messages first (foreign key)
sb.table("messages").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
print("✅ Messages deleted.")

# Delete all users
sb.table("users").delete().neq("phone", "XXXXXX").execute()
print("✅ Users deleted.")

# Count after
users_after  = sb.table("users").select("phone", count="exact").execute()
msgs_after   = sb.table("messages").select("id", count="exact").execute()
print(f"\nAFTER:")
print(f"  users    : {users_after.count}")
print(f"  messages : {msgs_after.count}")
print("\n🚀 DB is clean. Fresh start ready!")
