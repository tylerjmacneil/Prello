
from fastapi import FastAPI, Depends
from app.deps import get_user

app = FastAPI(title="Prello API (minimal)")

@app.get("/")
def root():
	return {"name": "prello-api-min"}

@app.get("/health")
def health():
	return {"ok": True}

@app.get("/me")
async def me(user=Depends(get_user)):
	return {"user_id": user["id"]}
