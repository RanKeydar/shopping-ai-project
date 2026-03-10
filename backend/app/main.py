import time
from fastapi import FastAPI

from app import models  # noqa: F401  <-- חשוב: טוען את המודלים

from app.api.routes.items import router as items_router
from app.db import Base, engine, SessionLocal
from app.api.routes.auth import router as auth_router

app = FastAPI()

app.include_router(items_router)
app.include_router(auth_router)


@app.on_event("startup")
def on_startup():
    # MySQL sometimes needs a few seconds after container is "up"
    for attempt in range(1, 21):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception as e:
            print(f"[startup] DB not ready (attempt {attempt}/20): {e}")
            time.sleep(1)
    else:
        raise RuntimeError("DB not ready after retries")

    # seed data if empty
    from app.db.init_db import seed_if_empty  # import here to avoid cycles
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()