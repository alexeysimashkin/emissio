from fastapi import FastAPI
from app.api.v1.endpoints import auth, patients, schedule, appointments, medical_records, procedures, analytics, max_webhook
from app.core.database import engine, Base
from app.core.init_db import init_admin

app = FastAPI(title="ЕМИССиО", version="1.0.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_admin()

# Регистрация роутеров
app.include_router(auth.router, prefix="/api/v1")
app.include_router(patients.router, prefix="/api/v1")
app.include_router(schedule.router, prefix="/api/v1")
app.include_router(appointments.router, prefix="/api/v1")
app.include_router(medical_records.router, prefix="/api/v1")
app.include_router(procedures.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(max_webhook.router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "system": "ЕМИССиО"}
