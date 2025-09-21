
from fastapi import APIRouter, Request, HTTPException, Depends
from .utils import verify_stripe_signature, rate_limiter


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/webhook")
async def payments_webhook(
    req: Request,
    _=Depends(rate_limiter),
):
    payload = await req.body()
    sig = req.headers.get("stripe-signature", "")
    event = verify_stripe_signature(payload, sig)

    # handle a couple of common events
    t = event["type"]
    data = event["data"]["object"]
    if t == "checkout.session.completed":
        # TODO: mark job as paid using data["id"] / metadata
        pass
    elif t == "payment_intent.succeeded":
        # TODO: update payment status
        pass

    # handle events...
    return {"ok": True}
