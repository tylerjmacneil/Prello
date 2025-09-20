import os
from supabase import create_client, Client
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
security = HTTPBearer()

async def get_user(authorization: str = Depends(security)):
    if not authorization or not authorization.credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.credentials
    user_resp = sb.auth.get_user(token)
    if not user_resp or not user_resp.user:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = user_resp.user
    auth_user_id = user.id
    email = user.email
    # Check if user exists in public.users
    users = sb.table("users").select("*").eq("auth_user_id", auth_user_id).execute()
    if not users.data:
        # Insert new user
        insert_resp = sb.table("users").insert({"auth_user_id": auth_user_id, "email": email}).execute()
        user_row = insert_resp.data[0]
    else:
        user_row = users.data[0]
    return user_row
