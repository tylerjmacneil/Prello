from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import create_client
import os

from ..auth import get_current_user  # relative import

router = APIRouter(prefix="/jobs", tags=["jobs"])

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# --- Request models ---
class JobCreate(BaseModel):
    client_id: str
    title: str
    description: Optional[str] = None
    price_cents: int
    bnpl_enabled: bool = False
    pass_fees: bool = False
    status: Optional[str] = "draft"  # 'draft'|'sent'|'signed'|'paid'|'cancelled'

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price_cents: Optional[int] = None
    bnpl_enabled: Optional[bool] = None
    pass_fees: Optional[bool] = None
    status: Optional[str] = None

# --- Endpoints ---
@router.get("/")
def list_jobs(user=Depends(get_current_user)):
    resp = (
        supabase.table("jobs")
        .select("*")
        .eq("owner_user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data

@router.post("/")
def create_job(payload: JobCreate, user=Depends(get_current_user)):
    if payload.price_cents < 0:
        raise HTTPException(status_code=422, detail="price_cents must be >= 0")

    job = payload.model_dump()
    job["owner_user_id"] = user["id"]
    job.setdefault("status", "draft")

    resp = supabase.table("jobs").insert(job).execute()
    if not resp.data:
        raise HTTPException(status_code=400, detail="Failed to create job")
    return resp.data[0]

@router.get("/{job_id}")
def get_job(job_id: str, user=Depends(get_current_user)):
    resp = (
        supabase.table("jobs")
        .select("*")
        .eq("id", job_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return resp.data[0]

@router.patch("/{job_id}")
def update_job(job_id: str, update: JobUpdate, user=Depends(get_current_user)):
    data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=422, detail="No fields to update")

    resp = (
        supabase.table("jobs")
        .update(data)
        .eq("id", job_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Job not found or no changes")
    return resp.data[0]

@router.delete("/{job_id}")
def delete_job(job_id: str, user=Depends(get_current_user)):
    (
        supabase.table("jobs")
        .delete()
        .eq("id", job_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    return {"ok": True}
from fastapi import APIRouter, Depends, HTTPException
from supabase import create_client
import os

from ..auth import get_current_user  # relative import

router = APIRouter(prefix="/jobs", tags=["jobs"])

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# GET /jobs
@router.get("/")
def list_jobs(user=Depends(get_current_user)):
    resp = (
        supabase.table("jobs")
        .select("*")
        .eq("owner_user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data

# POST /jobs
@router.post("/")
def create_job(job: dict, user=Depends(get_current_user)):
    # Minimal validation
    for key in ["client_id", "title", "price_cents"]:
        if key not in job:
            raise HTTPException(status_code=422, detail=f"Missing field: {key}")

    job["owner_user_id"] = user["id"]
    job.setdefault("status", "draft")          # expected enum in DB
    job.setdefault("bnpl_enabled", False)
    job.setdefault("pass_fees", False)

    resp = supabase.table("jobs").insert(job).execute()
    if not resp.data:
        raise HTTPException(status_code=400, detail="Failed to create job")
    return resp.data[0]

# GET /jobs/{job_id}
@router.get("/{job_id}")
def get_job(job_id: str, user=Depends(get_current_user)):
    resp = (
        supabase.table("jobs")
        .select("*")
        .eq("id", job_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return resp.data[0]

# PATCH /jobs/{job_id}
@router.patch("/{job_id}")
def update_job(job_id: str, update: dict, user=Depends(get_current_user)):
    # keep ownership enforced
    resp = (
        supabase.table("jobs")
        .update(update)
        .eq("id", job_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Job not found or no changes")
    return resp.data[0]

# DELETE /jobs/{job_id}
@router.delete("/{job_id}")
def delete_job(job_id: str, user=Depends(get_current_user)):
    (
        supabase.table("jobs")
        .delete()
        .eq("id", job_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    return {"ok": True}
