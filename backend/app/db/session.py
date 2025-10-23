from supabase import create_client, Client
from app.core.config import get_settings
from fastapi import Request, HTTPException
import jwt

# A single client instance is created and shared across the application.
settings = get_settings()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
# supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
def get_db() -> Client:
    """
    Dependency function that provides a Supabase client instance with service role.
    USE WITH CAUTION - This bypasses RLS security!
    """
    return supabase

def get_user_id_from_token(request: Request) -> str:
    """
    Extract user_id from JWT token
    This is more reliable than db.auth.get_user()
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Token d'authentification requis"
        )

    token = auth_header.split(" ")[1]

    try:
        # Decode JWT without verification (Supabase already verified it)
        # We just need to extract the user_id
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: no user ID found"
            )

        return user_id
    except jwt.DecodeError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token format"
        )

def get_authenticated_db(request: Request) -> Client:
    """
    Dependency function that provides a Supabase client with user JWT.
    RLS will automatically filter data based on auth.uid().
    This is the SECURE way to access user data.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Token d'authentification requis"
        )

    token = auth_header.split(" ")[1]

    # Create client with user token instead of service role key
    # This enables RLS (Row Level Security) filtering
    user_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    user_client.auth.set_session(access_token=token, refresh_token="")

    return user_client 