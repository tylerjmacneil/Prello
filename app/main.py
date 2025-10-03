from fastapi import FastAPI
from app.routers import clients, jobs

app = FastAPI(title="Prello API")
app.include_router(clients.router)
app.include_router(jobs.router)

@app.get("/healthz")
def healthz():
    return {"ok": True}
