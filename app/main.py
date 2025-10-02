import os, time
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import jwt
from jwt import PyJWKClient
from app.routers import clients

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL", f"{SUPABASE_URL}/auth/v1/keys")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")  # <-- NEW
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app = FastAPI(title="Prello API", version="0.1.0")
app.include_router(clients.router)

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
    import time as _time
    global _jwks_client, _jwks_cached_at
    now = _time.time()
    if _jwks_client is None or now - _jwks_cached_at > _JWKS_TTL:
        if not SUPABASE_JWKS_URL:
            raise RuntimeError("SUPABASE_JWKS_URL not set")
        _jwks_client = PyJWKClient(SUPABASE_JWKS_URL)
        _jwks_cached_at = now
    return _jwks_client

def _decode_supabase_jwt(token: str):
    """Supports HS256 (JWT secret) and RS256 (JWKS) Supabase tokens."""
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")

        issuer = f"{SUPABASE_URL}/auth/v1" if SUPABASE_URL else None

        if alg == "HS256":
            if not SUPABASE_JWT_SECRET:
                raise HTTPException(status_code=500, detail="Server missing SUPABASE_JWT_SECRET")
            return jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"require": ["exp", "iat"], "verify_aud": False},
                issuer=issuer if issuer else None,
            )
        else:
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token).key
            return jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                options={"require": ["exp", "iat"], "verify_aud": False},
                issuer=issuer if issuer else None,
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

def get_current_user(request: Request):
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth.split(" ", 1)[1].strip()
    claims = _decode_supabase_jwt(token)
    return {"user_id": claims.get("sub"), "email": claims.get("email"), "role": claims.get("role")}

@app.get("/health")
def health(): 
    return {"ok": True}

@app.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user["user_id"], "email": user["email"], "role": user["role"]}
