
import os
import time
import stripe
from fastapi import Request, HTTPException

# Optional but nice to pin:
stripe.api_version = "2024-06-20"

# Simple in-memory rate limiter (per-IP)
_BUCKET: dict[str, tuple[int, int]] = {}   # key -> (window_start_ts, count)
RATE = 30     # requests
WINDOW = 60   # seconds

async def rate_limiter(request: Request):
    key = request.client.host or "unknown"
    now = int(time.time())
    w, c = _BUCKET.get(key, (now, 0))
    if now - w >= WINDOW:
        _BUCKET[key] = (now, 1)
        return
    if c + 1 > RATE:
        raise HTTPException(status_code=429, detail="Too many requests")
    _BUCKET[key] = (w, c + 1)

def verify_stripe_signature(payload: bytes, sig_header: str):
    """Return a Stripe Event or raise HTTP 400 if verification fails."""
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        # Fail fast if env var missing
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=secret,
            tolerance=300,  # seconds
        )
        return event
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")
