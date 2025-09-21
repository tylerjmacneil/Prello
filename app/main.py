

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .deps import get_user
import jwt

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



@app.get("/me")
def me(authorization: str = Header(...)):
	from .config import settings
	if not authorization.lower().startswith("bearer "):
		raise HTTPException(status_code=401, detail="Missing bearer token")
	token = authorization.split(" ", 1)[1]
	try:
		payload = jwt.decode(token, settings.SUPABASE_ANON_KEY, algorithms=["HS256"])
		user_id = payload.get("sub")
		email = payload.get("email")
		if not user_id:
			raise HTTPException(status_code=401, detail="Invalid token payload")
		return {"user_id": user_id, "email": email}
	except Exception as e:
		raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")


from .clients import router as clients_router
from .jobs import router as jobs_router
from .payments import router as payments_router
from .stripe_webhook import router as stripe_router
app.include_router(clients_router)
app.include_router(jobs_router)
app.include_router(payments_router)
app.include_router(stripe_router)
