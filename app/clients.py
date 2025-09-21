
from fastapi import APIRouter, Depends
from .deps import get_sb, get_current_user_id
from .models import ClientIn

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("")
async def list_clients(user_id: str = Depends(get_current_user_id)):
    sb = get_sb()
    r = sb.table("clients").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return r.data


@router.post("")
async def create_client(payload: ClientIn, user_id: str = Depends(get_current_user_id)):
    sb = get_sb()
    res = sb.table("clients").insert(
        {"user_id": user_id, **payload.model_dump()},
        returning="representation",
    ).execute()
    if res.data and len(res.data) == 1:
        return res.data[0]
    raise HTTPException(status_code=500, detail="Insert failed")
