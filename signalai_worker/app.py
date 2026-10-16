from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI, HTTPException

from signalai_worker.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        yield
    finally:
        await pool.close()


app = FastAPI(title="SignalAI Worker", version=settings.service_version, lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/ready")
async def ready() -> dict[str, str]:
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        await pool.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="redis_unavailable") from exc
    finally:
        await pool.close()
    return {"status": "ready", "service": settings.service_name}
