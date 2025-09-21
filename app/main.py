

from fastapi import FastAPI, Depends, Header, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .deps import get_user
import jwt


bearer = HTTPBearer(auto_error=True)
app = FastAPI(title="Prello API", version="1.0.0")

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
async def me(creds: HTTPAuthorizationCredentials = Security(bearer)):
	token = creds.credentials
	return {"has_token": bool(token)}

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
