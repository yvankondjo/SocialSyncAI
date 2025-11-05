from supabase import create_client, Client, acreate_client, AsyncClient
from app.core.config import get_settings
from fastapi import Request, HTTPException
import jwt

settings = get_settings()

supabase: Client = create_client(
    settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
)

_async_supabase: AsyncClient | None = None


def get_db() -> Client:
    """
    Dependency function that provides a Supabase client instance with service role.
    USE WITH CAUTION - This bypasses RLS security!

    DEPRECATED: Use get_async_db() for new code to benefit from async performance.
    """
    return supabase


async def get_async_db() -> AsyncClient:
    """
    Returns the async Supabase client for high-performance async operations.

    The client is created lazily on first call and reused for subsequent calls.
    This client uses service role key and bypasses RLS - use with caution!

    Returns:
        AsyncClient: Async Supabase client instance
    """
    global _async_supabase
    if _async_supabase is None:
        _async_supabase = await acreate_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
        )
    return _async_supabase


async def close_async_db():
    """
    Closes the async Supabase client connection.
    Should be called during application shutdown.
    """
    global _async_supabase
    if _async_supabase is not None:
        await _async_supabase.close()
        _async_supabase = None


def get_authenticated_db(request: Request) -> Client:
    """
    Dependency function that provides a Supabase client with user JWT.
    RLS will automatically filter data based on auth.uid().
    This is the SECURE way to access user data.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token d'authentification requis")

    token = auth_header.split(" ")[1]

    user_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    user_client.auth.set_session(access_token=token, refresh_token="")

    return user_client
