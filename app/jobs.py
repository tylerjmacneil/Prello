from fastapi import APIRouter, Depends, HTTPException, Query
from .deps import get_sb, get_user
from .models import JobIn

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("")
async def list_jobs(status: str | None = Query(default=None), user = Depends(get_user)):
    sb = get_sb()
    q = sb.table("jobs").select("*").eq("user_id", user["id"])
    if status:
        q = q.eq("status", status)
    return q.order("created_at", desc=True).execute().data

@router.post("")
async def create_job(payload: JobIn, user = Depends(get_user)):
    sb = get_sb()
    c = sb.table("clients").select("id,user_id").eq("id", payload.client_id).single().execute()
    if not c.data or c.data["user_id"] != user["id"]:
        raise HTTPException(status_code=400, detail="Client not found or not yours")
    r = sb.table("jobs").insert({"user_id": user["id"], **payload.model_dump()}).select("*").execute()
    return r.data[0]
