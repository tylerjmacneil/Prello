import time
from fastapi import Request, HTTPException
from collections import defaultdict

RATE_LIMIT = 30  # requests
RATE_PERIOD = 60  # seconds

# {ip: [timestamps]}
_ip_requests = defaultdict(list)

def rate_limiter(request: Request):
    ip = request.client.host
    now = time.time()
    window_start = now - RATE_PERIOD
    # Remove old timestamps
    _ip_requests[ip] = [t for t in _ip_requests[ip] if t > window_start]
    if len(_ip_requests[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    _ip_requests[ip].append(now)
