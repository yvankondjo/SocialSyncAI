import os
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

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or not SUPABASE_ANON_KEY or not SUPABASE_JWT_SECRET:
        raise ValueError("SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY and SUPABASE_JWT_SECRET environment variables are required")

def get_settings() -> Settings:
    settings = Settings() 
    return settings
