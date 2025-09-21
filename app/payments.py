import stripe
from fastapi import APIRouter, Depends, HTTPException
from .deps import get_sb, get_current_user_id
from .config import settings

router = APIRouter(prefix="/jobs", tags=["payments"])
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/{job_id}/checkout")
async def create_checkout(job_id: str, user_id: str = Depends(get_current_user_id)):
    sb = get_sb()
    job = sb.table("jobs").select("*").eq("id", job_id).single().execute().data
    if not job or job["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Job not found or not yours")

    total = job.get("total") or job.get("price_cents")
    if not total:
        raise HTTPException(status_code=400, detail="Job missing total/price_cents")

    sess = stripe.checkout.Session.create(
        mode="payment",
        currency=settings.STRIPE_CURRENCY,
        line_items=[{
            "price_data": {
                "currency": settings.STRIPE_CURRENCY,
                "product_data": {"name": job["title"]},
                "unit_amount": total,
            },
            "quantity": 1,
        }],
        success_url=settings.SUCCESS_URL,
        cancel_url=settings.CANCEL_URL,
        automatic_payment_methods={"enabled": True}
    )
    sb.table("jobs").update({"checkout_session_id": sess.id}).eq("id", job_id).execute()
    return {"checkout_url": sess.url}
