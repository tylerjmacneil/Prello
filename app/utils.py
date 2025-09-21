from fastapi import Request, HTTPException
import time

_BUCKET = {}  # { key: [window_start_ts, count] }
RATE = 30
WINDOW = 60  # seconds

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
