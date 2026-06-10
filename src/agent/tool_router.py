"""Tool Router: despacha tool calls a las Cloud Functions o Mock API."""

import os
import time
import uuid
from datetime import datetime, timezone

import httpx
import structlog

from src.models.schemas import ToolResponse

logger = structlog.get_logger()

# Mapeo de tools a endpoints
TOOL_ENDPOINTS = {
    "sheets_reader": "/api/v1/sheets/read",
    "sheets_writer": "/api/v1/sheets/write",
    "calculator": "/api/v1/calc",
    "report_generator": "/api/v1/report",
}


class ToolRouter:
    """Despacha tool calls al backend correspondiente."""

    def __init__(self):
        self.base_url = os.getenv("TOOLS_BASE_URL", "http://mock-sheets-api:8001")
        self.timeout = float(os.getenv("TOOL_TIMEOUT", "30"))

    async def execute(self, tool_name: str, tool_args: dict, request_id: str) -> ToolResponse:
        """Ejecuta un tool call y retorna el resultado."""
        endpoint = TOOL_ENDPOINTS.get(tool_name)
        if not endpoint:
            return ToolResponse(
                status="error",
                error={"code": "UNKNOWN_TOOL", "message": f"Tool '{tool_name}' no existe."},
            )

        url = f"{self.base_url}{endpoint}"
        payload = {
            "request_id": f"{request_id}-{tool_name}-{uuid.uuid4().hex[:6]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": tool_args,
        }

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                latency_ms = int((time.time() - start_time) * 1000)

                data = response.json()

                logger.info(
                    "tool_call",
                    tool=tool_name,
                    status_code=response.status_code,
                    latency_ms=latency_ms,
                    request_id=request_id,
                )

                if response.status_code >= 400:
                    return ToolResponse(
                        status="error",
                        error=data.get("error", {"code": "TOOL_ERROR", "message": "Error en el tool"}),
                        latency_ms=latency_ms,
                    )

                return ToolResponse(
                    status="success",
                    data=data.get("data", data),
                    latency_ms=latency_ms,
                )

        except httpx.TimeoutException:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error("tool_timeout", tool=tool_name, latency_ms=latency_ms)
            return ToolResponse(
                status="error",
                error={"code": "TIMEOUT", "message": f"Tool '{tool_name}' no respondió en {self.timeout}s."},
                latency_ms=latency_ms,
            )

        except httpx.ConnectError:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error("tool_connection_error", tool=tool_name)
            return ToolResponse(
                status="error",
                error={"code": "CONNECTION_ERROR", "message": f"No se puede conectar con '{tool_name}'."},
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error("tool_unexpected_error", tool=tool_name, error=str(e))
            return ToolResponse(
                status="error",
                error={"code": "INTERNAL_ERROR", "message": str(e)},
                latency_ms=latency_ms,
            )
