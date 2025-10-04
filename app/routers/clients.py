from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from supabase import create_client
import os

from ..auth import get_current_user  # relative import

router = APIRouter(prefix="/clients", tags=["clients"])

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None  # relaxed to plain string for dev
    phone: Optional[str] = None

@router.get("/")
def list_clients(user=Depends(get_current_user)):
    resp = supabase.table("clients").select("*").eq("owner_user_id", user["id"]).execute()
    return resp.data

@router.post("/")
def create_client_route(client: ClientCreate, user=Depends(get_current_user)):
    data = client.model_dump()
    data["owner_user_id"] = user["id"]
    try:
        resp = supabase.table("clients").insert(data).execute()
    except Exception as e:
        # Surface DB error during dev so you know exactly what's wrong
        raise HTTPException(status_code=400, detail=f"Insert failed: {e}")
    if not resp.data:
        raise HTTPException(status_code=400, detail="Failed to create client")
    return resp.data[0]

@router.get("/{client_id}")
def get_client(client_id: str, user=Depends(get_current_user)):
    resp = (
        supabase.table("clients")
        .select("*")
        .eq("id", client_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Client not found")
    return resp.data[0]

@router.patch("/{client_id}")
def update_client(client_id: str, update: dict, user=Depends(get_current_user)):
    resp = (
        supabase.table("clients")
        .update(update)
        .eq("id", client_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Client not found or no changes")
    return resp.data[0]

@router.delete("/{client_id}")
def delete_client(client_id: str, user=Depends(get_current_user)):
    supabase.table("clients").delete().eq("id", client_id).eq("owner_user_id", user["id"]).execute()
    return {"ok": True}
