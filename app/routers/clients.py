from fastapi import APIRouter, Depends, HTTPException
from supabase import create_client
import os

from ..auth import get_current_user  # <-- relative import

router = APIRouter(prefix="/clients", tags=["clients"])

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

@router.get("/")
def list_clients(user=Depends(get_current_user)):
    resp = supabase.table("clients").select("*").eq("owner_user_id", user["id"]).execute()
    return resp.data
