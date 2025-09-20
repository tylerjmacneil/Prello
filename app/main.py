from fastapi import FastAPI
app = FastAPI(title="Prello API (minimal)")
@app.get("/")
def root(): return {"name": "prello-api-min"}
@app.get("/health")
def health(): return {"ok": True}
