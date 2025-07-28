from supabase import create_client, Client
from app.core.config import get_settings

# A single client instance is created and shared across the application.
settings = get_settings()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

def get_db() -> Client:
    """
    Dependency function that provides a Supabase client instance.
    """
    return supabase 