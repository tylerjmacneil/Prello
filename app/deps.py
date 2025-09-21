import os
from fastapi import Header, HTTPException
from typing import Dict, Any
from supabase import create_client, Client
from .config import settings

sb: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

async def get_user(authorization: str = Header(...)) -> Dict[str, Any]:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    u = sb.auth.get_user(token)
    if not u or not u.user:
        raise HTTPException(status_code=401, detail="Invalid token")

    auth_user_id = u.user.id
    email = u.user.email or ""

    # ensure users row exists
    row = sb.table("users").select("*").eq("auth_user_id", auth_user_id).single().execute()
    if not row.data:
        created = sb.table("users").insert({"auth_user_id": auth_user_id, "email": email}).execute()
        data = created.data[0]
    else:
        data = row.data
    return data  # includes users.id
