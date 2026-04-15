from app.db.supabase import get_supabase

def get_db():
    return get_supabase()
