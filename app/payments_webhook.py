import stripe
from fastapi import APIRouter, Request, HTTPException
from .deps import get_sb
from .config import settings

router = APIRouter(prefix="/payments", tags=["payments"])
stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/webhook")
async def payments_webhook(req: Request):
    sb = get_sb()
    payload = await req.body()
    sig = req.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")

    if event["type"] == "checkout.session.completed":
        obj = event["data"]["object"]
        sid = obj["id"]
        amount = obj.get("amount_total")
        email = obj.get("customer_email")
        job = sb.table("jobs").select("id").eq("checkout_session_id", sid).single().execute().data
        if job:
            sb.table("jobs").update({"paid": True}).eq("id", job["id"]).execute()
            sb.table("payments").upsert({
                "id": sid,
                "amount": amount,
                "customer_email": email
            }).execute()
    return {"ok": True}
