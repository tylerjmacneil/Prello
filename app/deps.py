from functools import lru_cache
from typing import Dict, Any
from fastapi import Header, HTTPException
from supabase import create_client, Client
from .config import settings

@lru_cache
def get_sb() -> Client:
    url = (settings.SUPABASE_URL or "").strip()
    key = (settings.SUPABASE_SERVICE_ROLE_KEY or "").strip()
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase not configured: set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)

async def get_user(authorization: str = Header(...)) -> Dict[str, Any]:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    sb = get_sb()
    u = sb.auth.get_user(token)
    if not u or not u.user:
        raise HTTPException(status_code=401, detail="Invalid token")
    auth_user_id = u.user.id
    email = u.user.email or ""
    row = sb.table("users").select("*").eq("auth_user_id", auth_user_id).single().execute()
    data = row.data if row.data else sb.table("users").insert({"auth_user_id": auth_user_id, "email": email}).execute().data[0]
    return data
