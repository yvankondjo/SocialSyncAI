import os
from dotenv import load_dotenv

# It's better to load dotenv once at the application's entry point,
# but for modularity, we can call it here.
load_dotenv()

class Settings:
    PROJECT_NAME: str = "SocialSync AI"
    PROJECT_VERSION: str = "1.0.0"

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required")

settings = Settings() 