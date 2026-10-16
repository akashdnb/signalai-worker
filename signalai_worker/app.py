from fastapi import FastAPI

from signalai_worker.config import settings

app = FastAPI(title="SignalAI Worker", version=settings.service_version)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/ready")
async def ready() -> dict[str, str]:
    # Queue dependency checks will be added before production deployment.
    return {"status": "ready", "service": settings.service_name}
