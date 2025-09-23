
from fastapi import APIRouter, Request, HTTPException, Depends
import stripe
from .config import settings
from .deps import get_sb
from postgrest.exceptions import APIError


router = APIRouter(tags=["payments"])


@router.post("/payments/webhook")
async def payments_webhook(req: Request, sb = Depends(get_sb)):
    sig = req.headers.get("stripe-signature", "")
    payload = await req.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle successful checkout
    if event["type"] == "checkout.session.completed":
        cs = event["data"]["object"]
        job_id = (cs.get("metadata") or {}).get("job_id")
        if job_id:
            try:
                # keep it conservative: just set paid_at timestamp
                res = sb.table("jobs").update({"paid_at": "now()"}).eq("id", job_id).execute()
                # (optional) if your status enum allows 'scheduled' or 'paid', you can also set it:
                # sb.table("jobs").update({"status": "scheduled", "paid_at": "now()"}).eq("id", job_id).execute()
            except APIError as e:
                # Log only; don’t fail the webhook (Stripe will retry on 4xx/5xx)
                print("Webhook update failed:", getattr(e, "message", str(e)))

    return {"ok": True}
