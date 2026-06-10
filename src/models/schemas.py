"""Pydantic models para request/response del agente BrewFinance."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Request Models ───

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Mensaje del usuario")


class ToolCallInput(BaseModel):
    request_id: str
    timestamp: str
    payload: dict


# ─── Response Models ───

class ChatResponse(BaseModel):
    request_id: str
    message: str
    model_used: str
    steps: int
    latency_ms: int
    tool_calls: list[str] = []


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "brewfinance-orchestrator"
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─── Tool Response Models ───

class ToolResponse(BaseModel):
    status: str  # "success" or "error"
    data: Optional[dict] = None
    error: Optional[dict] = None
    latency_ms: int = 0


# ─── Guardrail Models ───

class ValidationResult(BaseModel):
    is_valid: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    field: Optional[str] = None


# ─── ReAct Step Models ───

class ReActStep(BaseModel):
    step: int
    type: str  # "thought_action" or "answer"
    thought: Optional[str] = None
    tool_name: Optional[str] = None
    tool_params: Optional[dict] = None
    tool_status: Optional[str] = None
    tool_latency_ms: Optional[int] = None
    answer: Optional[str] = None
