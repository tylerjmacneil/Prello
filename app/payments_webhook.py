
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

    # Handle payment events
    if event["type"] in ("checkout.session.completed", "payment_intent.succeeded"):
        obj = event["data"]["object"]
        meta = (obj.get("metadata") or {})
        job_id = meta.get("job_id")
        user_id = meta.get("user_id")
        amount = obj.get("amount_total") or obj.get("amount_received")  # in cents

        if not (job_id and user_id and amount):
            return {"ok": True}

        # 1) Insert payment
        try:
            sb.table("payments").insert({
                "user_id": user_id,
                "job_id": job_id,
                "amount_cents": int(amount),
                "kind": meta.get("kind", "progress"),
                "processor_ref": obj.get("payment_intent") or obj.get("id"),
            }).execute()
        except APIError as e:
            print("Payment insert failed:", getattr(e, "message", str(e)))

        # 2) Recalculate aggregates
        try:
            total = sb.rpc("sum_job_payments", {"p_job_id": job_id}).execute().data or 0
        except Exception:
            # fallback to SELECT sum if RPC fails
            total_res = sb.table("payments").select("amount_cents").eq("job_id", job_id).execute()
            total = sum(p.get("amount_cents", 0) for p in (total_res.data or []))

        # 3) Get job price
        job_res = sb.table("jobs").select("price_cents").eq("id", job_id).single().execute()
        job_price = job_res.data["price_cents"] if job_res.data and "price_cents" in job_res.data else 0

        # 4) Update job payment status
        try:
            sb.table("jobs").update({
                "amount_paid_cents": int(total),
                "payment_status": "paid" if int(total) >= job_price else "partial"
            }).eq("id", job_id).execute()
        except APIError as e:
            print("Job update failed:", getattr(e, "message", str(e)))

    return {"ok": True}
