from supabase import create_client, Client
from app.config import settings

_client: Client | None = None
_admin_client: Client | None = None

def get_supabase() -> Client:
    """Returns the standard Supabase client."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client

def get_supabase_admin() -> Client:
    """Returns the admin Supabase client (bypasses RLS)."""
    global _admin_client
    if _admin_client is None:
        # Using service key for admin actions
        _admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _admin_client
