from fastapi import FastAPI, HTTPException

from signalai_worker.config import settings
from signalai_worker.db import create_pool

app = FastAPI(title="SignalAI Worker", version=settings.service_version)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/ready")
async def ready() -> dict[str, str]:
    try:
        pool = await create_pool()
        try:
            await pool.fetchval("select 1")
        finally:
            await pool.close()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database_unavailable") from exc
    return {"status": "ready", "service": settings.service_name}
