from fastapi import APIRouter, Depends, HTTPException
from supabase import create_client
from app.auth import get_current_user
import os

router = APIRouter(prefix="/clients", tags=["clients"])

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

@router.get("/")
def list_clients(user=Depends(get_current_user)):
    resp = supabase.table("clients").select("*").eq("owner_user_id", user["id"]).execute()
    return resp.data

@router.post("/")
def create_client(client: dict, user=Depends(get_current_user)):
    client["owner_user_id"] = user["id"]
    resp = supabase.table("clients").insert(client).execute()
    return resp.data[0]

@router.get("/{client_id}")
def get_client(client_id: str, user=Depends(get_current_user)):
    resp = supabase.table("clients").select("*").eq("id", client_id).eq("owner_user_id", user["id"]).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Client not found")
    return resp.data[0]

@router.patch("/{client_id}")
def update_client(client_id: str, update: dict, user=Depends(get_current_user)):
    resp = supabase.table("clients").update(update).eq("id", client_id).eq("owner_user_id", user["id"]).execute()
    return resp.data[0] if resp.data else None

@router.delete("/{client_id}")
def delete_client(client_id: str, user=Depends(get_current_user)):
    supabase.table("clients").delete().eq("id", client_id).eq("owner_user_id", user["id"]).execute()
    return {"ok": True}
