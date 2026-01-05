import os
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv


load_dotenv()

class Settings:
    PROJECT_NAME: str = "SocialSync AI"
    PROJECT_VERSION: str = "1.0.0"

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    SUPABASE_JWT_ALGORITHM: str = "HS256"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    META_CONFIG_ID: str = os.getenv("META_CONFIG_ID", "test")
    META_GRAPH_VERSION: str = os.getenv("META_GRAPH_VERSION", "v24.0")
    WHATSAPP_REDIRECT_URI: str = os.getenv("WHATSAPP_REDIRECT_URI", "test")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "tests")

    # Configuration Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

    # Configuration Whop
    WHOP_API_KEY: str = os.getenv("WHOP_API_KEY", "")
    WHOP_WEBHOOK_SECRET: str = os.getenv("WHOP_WEBHOOK_SECRET", "")

    # Configuration Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "")

    # Configuration LangSmith
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "socialsync-ai")
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"


def canonicalize_redis_url(url: str) -> str:
    """
    Retourne l'URL Redis en s'assurant qu'une base (/0 par défaut) est présente.
    Préserve le schéma original (rediss:// pour SSL, redis:// sinon).
    Retire les paramètres SSL de la query string (gérés séparément par Celery/redis-py).
    """
    if not url:
        return url

    from urllib.parse import parse_qs, urlencode
    
    parsed = urlparse(url)
    # Préserver le schéma original (rediss:// ou redis://)
    original_scheme = parsed.scheme
    
    # Retirer les paramètres SSL de la query string (gérés via options de transport)
    query_params = parse_qs(parsed.query)
    ssl_params_removed = False
    for ssl_param in ['ssl_cert_reqs', 'ssl_ca_certs', 'ssl_certfile', 'ssl_keyfile', 'ssl']:
        if ssl_param in query_params:
            del query_params[ssl_param]
            ssl_params_removed = True
    
    # Reconstruire la query string sans les paramètres SSL
    new_query = urlencode(query_params, doseq=True) if query_params else ""
    
    # Ajouter "/0" si aucune base n'est explicitement définie
    path = parsed.path or ""
    if path in {"", "/"}:
        path = "/0"
    
    # Reconstruire l'URL en préservant le schéma original
    # Si l'URL initiale est en redis:// mais inclut des paramètres SSL, on
    # bascule explicitement le schéma en rediss:// pour éviter le conflit
    # « redis:// » + options SSL côté Celery/redis-py.
    scheme = parsed.scheme
    if scheme == "redis" and ssl_params_removed:
        scheme = "rediss"

    canonicalized = urlunparse((
        scheme,
        parsed.netloc,
        path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

    # S'assurer que le schéma est préservé (urlunparse devrait le faire, mais on vérifie)
    if original_scheme == "rediss" and not canonicalized.startswith("rediss://"):
        # Remplacer redis:// par rediss:// si nécessaire
        canonicalized = canonicalized.replace("redis://", "rediss://", 1)
    
    return canonicalized


def resolve_redis_url(url: str | None = None, *, source: str | None = None) -> str:
    """
    Résout et canonicalise une URL Redis en appliquant la base `/0` par défaut.
    Préserve le schéma rediss:// pour les connexions SSL.

    Args:
        url (str | None): URL explicite à utiliser en priorité (ex: variable d'env déjà
            fournie). Si absente, on retombe sur le couple CELERY_BROKER_URL / REDIS_URL.
        source (str | None): Nom logique de la source pour les logs (ex: "CELERY_BROKER_URL").

    Returns:
        str: URL Redis canonicalisée avec schéma préservé
    """
    import logging

    logger = logging.getLogger(__name__)
    
    # Priorité 0: URL explicite fournie en paramètre
    if url:
        masked_url = url.split('@')[0] + '@***' if '@' in url else url
        logger.info(f"✅ [RESOLVE_REDIS_URL] Using explicit URL from parameter: {masked_url}")
        return canonicalize_redis_url(url)
    
    celery_broker_url = os.getenv("CELERY_BROKER_URL", "")
    redis_url = os.getenv("REDIS_URL", "")
    
    # Log pour diagnostic
    logger.info(f"🔍 [RESOLVE_REDIS_URL] CELERY_BROKER_URL: {'SET' if celery_broker_url else 'NOT_SET'}")
    logger.info(f"🔍 [RESOLVE_REDIS_URL] REDIS_URL: {'SET' if redis_url else 'NOT_SET'}")
    
    selected_url = None
    
    # Priorité 1: CELERY_BROKER_URL (utilisé par Celery workers)
    if celery_broker_url:
        if redis_url and redis_url != celery_broker_url:
            logger.warning(
                f"⚠️ [RESOLVE_REDIS_URL] REDIS_URL et CELERY_BROKER_URL diffèrent. "
                f"Utilisation de CELERY_BROKER_URL pour garantir la cohérence avec les workers. "
                f"REDIS_URL sera ignoré."
            )
        masked_broker = celery_broker_url.split('@')[0] + '@***' if '@' in celery_broker_url else celery_broker_url
        logger.info(f"✅ [RESOLVE_REDIS_URL] Using CELERY_BROKER_URL: {masked_broker}")
        selected_url = celery_broker_url
    
    # Priorité 2: REDIS_URL (fallback si CELERY_BROKER_URL non défini)
    elif redis_url:
        masked_redis = redis_url.split('@')[0] + '@***' if '@' in redis_url else redis_url
        logger.info(f"✅ [RESOLVE_REDIS_URL] Using REDIS_URL: {masked_redis}")
        selected_url = redis_url
    
    # Priorité 3: Fallback localhost (dev uniquement)
    else:
        logger.warning(
            "⚠️ [RESOLVE_REDIS_URL] Ni REDIS_URL ni CELERY_BROKER_URL définis. "
            "Utilisation du fallback localhost (dev uniquement)."
        )
        return "redis://localhost:6379/0"
    
    # Canonicaliser l'URL en préservant le schéma (rediss:// ou redis://)
    if selected_url:
        return canonicalize_redis_url(selected_url)
    
    return selected_url

def get_settings() -> Settings:
    """Get settings instance with validation"""
    settings = Settings()
    
    # Validate required settings
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY or not settings.SUPABASE_ANON_KEY or not settings.SUPABASE_JWT_SECRET:
        import logging
        logger = logging.getLogger(__name__)
        missing = []
        if not settings.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not settings.SUPABASE_SERVICE_ROLE_KEY:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        if not settings.SUPABASE_ANON_KEY:
            missing.append("SUPABASE_ANON_KEY")
        if not settings.SUPABASE_JWT_SECRET:
            missing.append("SUPABASE_JWT_SECRET")
        error_msg = f"Missing required environment variables: {', '.join(missing)}"
        logger.error(f"❌ Configuration error: {error_msg}")
        raise ValueError(error_msg)
    
    return settings
