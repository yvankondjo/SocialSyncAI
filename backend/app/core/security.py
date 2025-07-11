import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

SECRET_KEY = os.getenv("SUPABASE_JWT_SECRET","")
if not SECRET_KEY:
    raise ValueError("No SUPABASE_JWT_SECRET set for JWT authentication")

ALGORITHM = "HS256"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Vous pouvez ajouter plus de validation ici (par ex. 'aud', 'iss')
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) 