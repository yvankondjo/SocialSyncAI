from supabase import create_client, Client
from app.core.config import get_settings
from fastapi import Request, HTTPException
import jwt

try:
    from supabase_auth.errors import AuthApiError
except ImportError:
    AuthApiError = Exception

try:
    settings = get_settings()
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Failed to initialize Supabase client: {e}")
    logger.error("Application will not start without valid Supabase configuration")
    raise

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

    try:
        user_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        user_client.auth.set_session(access_token=token, refresh_token="")
        return user_client
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        
        error_message = str(e)
        error_type = type(e).__name__
        error_repr = repr(e)
        
        logger.warning(
            f"Erreur authentification Supabase: type={error_type}, message={error_message[:200]}"
        )
        
        if (error_type == "AuthApiError" or 
            "does not exist" in error_message or 
            "User from sub claim" in error_message or
            "user does not exist" in error_message.lower() or
            "403" in error_repr or
            "Forbidden" in error_message):
            raise HTTPException(
                status_code=401,
                detail="L'utilisateur associé à ce token n'existe plus ou le token est invalide. Veuillez vous reconnecter.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if "invalid" in error_message.lower() or "expired" in error_message.lower() or "401" in error_repr:
            raise HTTPException(
                status_code=401,
                detail="Token d'authentification invalide ou expiré",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        raise HTTPException(
            status_code=401,
            detail="Erreur d'authentification. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"}
        ) 