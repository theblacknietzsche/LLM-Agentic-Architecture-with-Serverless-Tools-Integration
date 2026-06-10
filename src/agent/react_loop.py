"""Ciclo ReAct (Reason + Act): núcleo del agente BrewFinance."""

import os
import time
import structlog

from src.llm.gemini_client import GeminiClient
from src.agent.tool_router import ToolRouter
from src.agent.guardrails import validate_tool_call
from src.models.schemas import ChatResponse, ReActStep

logger = structlog.get_logger()

MAX_REACT_STEPS = int(os.getenv("MAX_REACT_STEPS", "5"))


class ReActAgent:
    """Agente conversacional con ciclo ReAct + tool-calling."""

    def __init__(self):
        self.llm = GeminiClient()
        self.tool_router = ToolRouter()
        self.sessions: dict[str, list[dict]] = {}  # session_id → historial

    async def chat(self, message: str, request_id: str, session_id: str = "default") -> ChatResponse:
        """Procesa un mensaje del usuario a través del ciclo ReAct."""
        start_time = time.time()
        steps: list[ReActStep] = []
        tool_calls_log: list[str] = []

        # Obtener o crear historial de sesión (máx 5 turnos)
        history = self.sessions.get(session_id, [])

        # Seleccionar modelo (small-first)
        model = self.llm.select_model(message)

        # ─── Ciclo ReAct ───
        current_message = message
        tool_results = None

        for step_num in range(1, MAX_REACT_STEPS + 1):
            # Llamar al LLM
            if tool_results:
                llm_response = await self.llm.generate(
                    message=current_message,
                    history=history,
                    tool_results=tool_results,
                    model_override=model,
                )
            else:
                llm_response = await self.llm.generate(
                    message=current_message,
                    history=history,
                    model_override=model,
                )

            # Caso 1: El LLM quiere llamar tools
            if llm_response["function_calls"]:
                tool_results = []

                for fc in llm_response["function_calls"]:
                    tool_name = fc["name"]
                    tool_args = fc["args"]

                    # Guardrail: validar antes de ejecutar
                    validation = validate_tool_call({"name": tool_name, "args": tool_args})

                    if not validation.is_valid:
                        logger.warning(
                            "guardrail_rejected",
                            tool=tool_name,
                            error_code=validation.error_code,
                            step=step_num,
                        )
                        tool_results.append({
                            "name": tool_name,
                            "response": {
                                "status": "error",
                                "error_code": validation.error_code,
                                "message": validation.error_message,
                            },
                        })
                        steps.append(ReActStep(
                            step=step_num,
                            type="guardrail_reject",
                            tool_name=tool_name,
                            tool_params=tool_args,
                            tool_status="rejected",
                        ))
                        continue

                    # Ejecutar tool
                    result = await self.tool_router.execute(tool_name, tool_args, request_id)

                    tool_calls_log.append(tool_name)
                    tool_results.append({
                        "name": tool_name,
                        "response": result.data if result.status == "success" else result.error,
                    })

                    steps.append(ReActStep(
                        step=step_num,
                        type="thought_action",
                        tool_name=tool_name,
                        tool_params=tool_args,
                        tool_status=result.status,
                        tool_latency_ms=result.latency_ms,
                    ))

                    logger.info(
                        "react_step",
                        step=step_num,
                        tool=tool_name,
                        status=result.status,
                        latency_ms=result.latency_ms,
                    )

                # Continuar el loop con los resultados
                continue

            # Caso 2: El LLM genera respuesta final (texto)
            if llm_response["text"]:
                answer = llm_response["text"]
                steps.append(ReActStep(
                    step=step_num,
                    type="answer",
                    answer=answer,
                ))

                # Actualizar historial de sesión
                history.append({"role": "user", "content": message})
                history.append({"role": "model", "content": answer})
                # Mantener solo últimos 5 turnos (10 mensajes)
                self.sessions[session_id] = history[-10:]

                total_latency = int((time.time() - start_time) * 1000)

                logger.info(
                    "react_complete",
                    request_id=request_id,
                    total_steps=len(steps),
                    total_latency_ms=total_latency,
                    model=model,
                    tool_calls=tool_calls_log,
                )

                return ChatResponse(
                    request_id=request_id,
                    message=answer,
                    model_used=model,
                    steps=len(steps),
                    latency_ms=total_latency,
                    tool_calls=tool_calls_log,
                )

        # Si se alcanzó el límite de pasos
        total_latency = int((time.time() - start_time) * 1000)
        logger.warning("react_max_steps", request_id=request_id, steps=MAX_REACT_STEPS)

        return ChatResponse(
            request_id=request_id,
            message=(
                "No pude completar el análisis en los pasos disponibles. "
                "¿Puedes reformular tu pregunta de forma más específica?"
            ),
            model_used=model,
            steps=MAX_REACT_STEPS,
            latency_ms=total_latency,
            tool_calls=tool_calls_log,
        )
