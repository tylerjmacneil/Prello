
from fastapi import APIRouter, Depends, HTTPException, Query
from postgrest.exceptions import APIError
from .deps import get_sb, get_current_user_id
from .models import JobIn

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(status: str | None = Query(default=None), user_id: str = Depends(get_current_user_id)):
    sb = get_sb()
    q = sb.table("jobs").select("*").eq("user_id", user_id)
    if status:
        q = q.eq("status", status)
    return q.order("created_at", desc=True).execute().data


@router.post("")
async def create_job(payload: JobIn, user_id: str = Depends(get_current_user_id)):
    sb = get_sb()
    try:
        client = sb.table("clients")\
            .select("id")\
            .eq("id", payload.client_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
    except APIError as e:
        # PGRST116 = 0 rows with .single()
        if getattr(e, "code", None) == "PGRST116" or "0 rows" in str(e).lower():
            raise HTTPException(status_code=404, detail="client_not_found_or_not_owned")
        raise

    try:
        res = sb.table("jobs").insert({**payload.model_dump(), "user_id": user_id}).execute()
        return res.data[0]
    except APIError as e:
        raise HTTPException(status_code=403, detail=getattr(e, "message", str(e)))
    raise HTTPException(status_code=500, detail="Insert failed")
