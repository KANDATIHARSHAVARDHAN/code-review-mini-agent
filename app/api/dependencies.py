from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

security = HTTPBearer()

def get_gemini_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Accept either header bearer token or .env GEMINI_API_KEY
    token = credentials.credentials
    if token:
        return token
    env = os.getenv("GEMINI_API_KEY")
    if not env:
        raise HTTPException(status_code=401, detail="Missing Gemini API key")
    return env
