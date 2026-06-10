"""BrewFinance Agent — Orchestrator (FastAPI)."""

import os
import uuid
from contextlib import asynccontextmanager

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header

from src.agent.react_loop import ReActAgent
from src.models.schemas import ChatRequest, ChatResponse, HealthResponse

load_dotenv()
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# ─── Lifespan ───
agent: ReActAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    env = os.getenv("ENVIRONMENT", "development")
    logger.info("startup", environment=env)

    if env == "development" and not os.getenv("GOOGLE_API_KEY"):
        logger.warning("no_api_key", message="Corriendo sin API key — modo mock")
        agent = None
    else:
        agent = ReActAgent()

    yield
    logger.info("shutdown")


# ─── App ───
app = FastAPI(
    title="BrewFinance Agent",
    description="Agente financiero inteligente para microempresa de bebidas",
    version="1.0.0",
    lifespan=lifespan,
)

API_KEY = os.getenv("API_KEY", "dev-key-123")


# ─── Middleware de autenticación ───
def verify_api_key(x_api_key: str = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")


# ─── Endpoints ───

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check del orchestrator."""
    return HealthResponse()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, x_api_key: str = Header(default=None)):
    """Endpoint principal: recibe mensaje del usuario y retorna respuesta del agente."""
    verify_api_key(x_api_key)

    if agent is None:
        raise HTTPException(
            status_code=503,
            detail="Agente no disponible. Verifica la configuración de GOOGLE_API_KEY.",
        )

    request_id = f"req-{uuid.uuid4().hex[:12]}"
    logger.info("chat_request", request_id=request_id, message_length=len(request.message))

    try:
        response = await agent.chat(
            message=request.message,
            request_id=request_id,
        )
        return response

    except Exception as e:
        logger.error("chat_error", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
