import stripe
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import stripe

from .deps import get_current_user_id, get_sb
from .config import settings

router = APIRouter(prefix="/jobs", tags=["payments"])

class CheckoutSessionResp(BaseModel):
    url: str

@router.post("/{job_id}/checkout", response_model=CheckoutSessionResp)
async def create_checkout(job_id: str,
                          user_id: str = Depends(get_current_user_id),
                          sb = Depends(get_sb)):
    # 1) Load the job you own
    job_res = sb.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).single().execute()
    job = job_res.data
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # (optional) only allow payment for certain statuses
    if job["status"] not in ("active", "scheduled"):
        raise HTTPException(status_code=400, detail="Only active/scheduled jobs can be paid")

    # 2) Create a Checkout Session
    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        mode="payment",
        success_url=f"{settings.SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=settings.CANCEL_URL,
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": job["title"] or "Service"},
                "unit_amount": int(job["price_cents"]),
            },
            "quantity": 1,
        }],
        metadata={"job_id": job_id, "user_id": user_id},
    )

    return {"url": session.url}
