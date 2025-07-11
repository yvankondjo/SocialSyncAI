import os
from dotenv import load_dotenv


load_dotenv()

class Settings:
    PROJECT_NAME: str = "SocialSync AI"
    PROJECT_VERSION: str = "1.0.0"

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    SUPABASE_JWT_ALGORITHM: str = "HS256"
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or not SUPABASE_JWT_SECRET:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required")

def get_settings() -> Settings:
    settings = Settings() 
    return settings



