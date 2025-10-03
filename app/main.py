from fastapi import FastAPI
from app.routers import clients

app = FastAPI(title="Prello API")
app.include_router(clients.router)

@app.get("/healthz")
def healthz():
    return {"ok": True}
