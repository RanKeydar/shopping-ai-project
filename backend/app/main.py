import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine, SessionLocal
from app.api.routes.auth import router as auth_router
from app.api.routes.items import router as items_router
from app.api.routes.orders import router as orders_router
from app.api.routes.favorites import router as favorites_router
from app.api.routes.chat_assistant import router as chat_assistant_router
from app.api.routes.ml import router as ml_router
from app.api.routes import product_import
from app import models  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    for attempt in range(1, 21):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception as e:
            print(f"[startup] DB not ready (attempt {attempt}/20): {e}")
            await asyncio.sleep(1)
    else:
        raise RuntimeError("DB not ready after retries")

    from app.db.init_db import seed_if_empty

    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(items_router)
app.include_router(orders_router)
app.include_router(favorites_router)
app.include_router(chat_assistant_router)
app.include_router(ml_router)
app.include_router(product_import.router)