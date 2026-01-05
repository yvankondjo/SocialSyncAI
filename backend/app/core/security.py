from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import get_settings, Settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="ignore")

def get_current_user_id(
    token: str = Depends(oauth2_scheme), 
    settings: Settings = Depends(get_settings)
) -> str:
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé secrète JWT n'est pas configurée sur le serveur."
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.SUPABASE_JWT_ALGORITHM],
            audience="authenticated",
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except JWTError as e:
        raise credentials_exception