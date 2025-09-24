
from fastapi import APIRouter, Depends, HTTPException, Query
from postgrest.exceptions import APIError
from .deps import get_sb, get_current_user_id
from .models import JobCreate, JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])



@router.get("", response_model=list[JobOut])
async def list_jobs(user_id: str = Depends(get_current_user_id), sb = Depends(get_sb)):
    res = sb.table("jobs").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data or []



@router.post("", response_model=JobOut)
async def create_job(payload: JobCreate,
                     user_id: str = Depends(get_current_user_id),
                     sb = Depends(get_sb)):
    try:
        client = sb.table("clients")\
            .select("id")\
            .eq("id", payload.client_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
    except APIError as e:
        if getattr(e, "code", None) == "PGRST116" or "0 rows" in str(e).lower():
            raise HTTPException(status_code=404, detail="client_not_found_or_not_owned")
        raise

    res = sb.table("jobs").insert({"user_id": user_id, **payload.model_dump()}, returning="representation").execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="insert_failed")
    return res.data[0]

@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: str, user_id: str = Depends(get_current_user_id), sb = Depends(get_sb)):
    res = sb.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="not_found")
    return res.data
