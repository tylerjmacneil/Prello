import os, time
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import jwt
from jwt import PyJWKClient

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL", f"{SUPABASE_URL}/auth/v1/keys")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app = FastAPI(title="Prello API", version="0.1.0")

if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

_jwks_client: Optional[PyJWKClient] = None
_jwks_cached_at = 0.0
_JWKS_TTL = 300.0

def _get_jwks_client() -> PyJWKClient:
    global _jwks_client, _jwks_cached_at
    now = time.time()
    if _jwks_client is None or now - _jwks_cached_at > _JWKS_TTL:
        if not SUPABASE_JWKS_URL:
            raise RuntimeError("SUPABASE_JWKS_URL not set")
        _jwks_client = PyJWKClient(SUPABASE_JWKS_URL)
        _jwks_cached_at = now
    return _jwks_client

def get_current_user(request: Request):
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth.split(" ", 1)[1].strip()
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token).key
        issuer = f"{SUPABASE_URL}/auth/v1" if SUPABASE_URL else None
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            options={"require": ["exp", "iat"], "verify_aud": False},
            issuer=issuer if issuer else None,
        )
        return {"user_id": claims.get("sub"), "email": claims.get("email"), "role": claims.get("role")}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

@app.get("/health")
def health(): 
    return {"ok": True}

@app.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user["user_id"], "email": user["email"], "role": user["role"]}
