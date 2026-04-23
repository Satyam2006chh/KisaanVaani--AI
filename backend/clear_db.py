import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="backend/.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

def clear_database():
    if not url or not key:
        print("ERROR: SUPABASE_URL or SERVICE_KEY missing in .env")
        return

    supabase: Client = create_client(url, key)

    # Order matters due to potential foreign keys
    tables = ["messages", "users"]

    for table in tables:
        print(f"Cleaning table: {table}")
        try:
            # Delete all rows where id is not null (or phone for users)
            if table == "users":
                res = supabase.table(table).delete().neq("phone", "0000").execute()
            else:
                res = supabase.table(table).delete().neq("id", -1).execute()
            
            print(f"SUCCESS: {table} cleared.")
        except Exception as e:
            print(f"ERROR cleaning {table}: {str(e)}")

    print("\nDATABASE IS NOW FRESH AND READY!")

if __name__ == "__main__":
    clear_database()
