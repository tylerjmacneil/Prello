
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
    try:
        event = verify_stripe_signature(payload, sig)
    except HTTPException as e:
        raise e

    # handle events...
    return {"ok": True}
