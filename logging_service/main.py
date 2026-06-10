"""BrewFinance Logging Service — Recibe y almacena logs estructurados."""

import json
from datetime import datetime
from fastapi import FastAPI, Request

app = FastAPI(title="BrewFinance Logging Service", version="1.0.0")

# Almacenamiento en memoria (en producción → Cloud Logging)
LOG_STORE: list[dict] = []


@app.get("/health")
async def health():
    return {"status": "ok", "service": "logging-service", "log_count": len(LOG_STORE)}


@app.post("/log")
async def receive_log(request: Request):
    body = await request.json()
    entry = {
        "received_at": datetime.utcnow().isoformat(),
        **body,
    }
    LOG_STORE.append(entry)
    # Mantener solo últimos 1000 logs en memoria
    if len(LOG_STORE) > 1000:
        LOG_STORE.pop(0)
    return {"status": "ok", "log_id": len(LOG_STORE)}


@app.get("/logs")
async def get_logs(limit: int = 50, severity: str = None):
    results = LOG_STORE.copy()
    if severity:
        results = [l for l in results if l.get("severity", "").upper() == severity.upper()]
    return {"total": len(results), "logs": results[-limit:]}
