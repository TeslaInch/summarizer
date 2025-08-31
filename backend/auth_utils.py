from fastapi import HTTPException, Header
from jose import jwt
import os
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET = os.getenv("SUPABASE_KEY")

def verify_token(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]  # Expecting "Bearer <token>"
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
