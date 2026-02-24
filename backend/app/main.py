from fastapi import FastAPI
from app.api.routes.items import router as items_router

app = FastAPI(title="Shopping AI Project", version="0.1.0")
app.include_router(items_router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "ok", "service": "shopping-ai-backend"}