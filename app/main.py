

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .deps import get_user

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
	return {"ok": True}


@app.get("/me")
async def me(user = Depends(get_user)):
	return {"user_id": user["id"]}

from .clients import router as clients_router
from .jobs import router as jobs_router
app.include_router(clients_router)
app.include_router(jobs_router)
