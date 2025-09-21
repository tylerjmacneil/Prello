

from fastapi import FastAPI, Depends, Header, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client, Client
import os
import jwt
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .deps import get_user
import jwt


bearer_scheme = HTTPBearer()
app = FastAPI(title="Prello API", version="1.0.0")

def get_supabase() -> Client:
	url = os.environ.get("SUPABASE_URL")
	key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
	if not url or not key:
		raise HTTPException(status_code=500, detail="Supabase not configured")
	return create_client(url, key)

app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.CORS_ORIGINS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

@app.get("/")
def root():
	return {"name": "prello-api"}


@app.get("/health")
def health():
	from .config import settings
	return {
		"ok": True,
		"supabase_configured": bool((settings.SUPABASE_URL or "").strip() and (settings.SUPABASE_SERVICE_ROLE_KEY or "").strip())
	}






@app.get("/me", tags=["auth"])
def me(
	credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
	sb: Client = Depends(get_supabase)
):
	token = credentials.credentials
	try:
		# Decode without verification just to read claims
		payload = jwt.decode(token, options={"verify_signature": False})
		user_id = payload.get("sub")
		email = payload.get("email")
	except Exception:
		raise HTTPException(status_code=401, detail="Invalid JWT")

	if not user_id:
		raise HTTPException(status_code=401, detail="Missing user info in token")

	return {"id": user_id, "email": email}

@app.get("/me2", tags=["auth"])
async def me2(user = Depends(get_user)):
	return {"user_id": user["id"], "email": user.get("email", "")}


from .clients import router as clients_router
from .jobs import router as jobs_router
from .payments import router as payments_router
from .stripe_webhook import router as stripe_router
app.include_router(clients_router)
app.include_router(jobs_router)
app.include_router(payments_router)
app.include_router(stripe_router)
