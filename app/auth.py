from fastapi import Header, HTTPException
from typing import Optional
import jwt  # PyJWT

def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Expect: Authorization: Bearer <SUPABASE_JWT>
    Extracts the 'sub' claim (user id). For speed we do a non-verified decode.
    NOTE: In Phase 3+ we can verify signature with the JWKS if desired.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    try:
        # Decode without verifying signature to read claims (speedy MVP).
        # Supabase JWT has 'sub' as the user id.
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token (no sub)")
        return {"id": user_id, "claims": payload}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
