"""Cliente de Gemini (Vertex AI) con soporte dual-model (Flash + Pro)."""

import json
import os
import time
import structlog
from google import genai
from google.genai import types

from src.llm.prompts import SYSTEM_PROMPT, FALLBACK_KEYWORDS

logger = structlog.get_logger()


class GeminiClient:
    """Cliente para Gemini con estrategia small-first (Flash → Pro)."""

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY no configurada")

        self.client = genai.Client(api_key=api_key)
        self.default_model = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
        self.fallback_model = os.getenv("FALLBACK_MODEL", "gemini-2.5-pro")

        # Cargar tool schemas
        tools_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "config", "tools_schema.json"
        )
        with open(tools_path, "r") as f:
            self.tools_config = json.load(f)

    def select_model(self, message: str) -> str:
        """Selecciona modelo según complejidad del mensaje (small-first)."""
        message_lower = message.lower()
        for keyword in FALLBACK_KEYWORDS:
            if keyword in message_lower:
                logger.info("fallback_model_selected", keyword=keyword)
                return self.fallback_model
        return self.default_model

    async def generate(
        self,
        message: str,
        history: list[dict] = None,
        tool_results: list[dict] = None,
        model_override: str = None,
    ) -> dict:
        """Genera respuesta del LLM con soporte de function calling."""
        model = model_override or self.default_model
        start_time = time.time()

        # Construir contenido
        contents = []

        # Historial de conversación
        if history:
            for turn in history[-5:]:  # Ventana de 5 turnos
                contents.append(
                    types.Content(
                        role=turn["role"],
                        parts=[types.Part.from_text(text=turn["content"])],
                    )
                )

        # Mensaje actual o tool results
        if tool_results:
            parts = []
            for tr in tool_results:
                parts.append(
                    types.Part.from_function_response(
                        name=tr["name"],
                        response=tr["response"],
                    )
                )
            contents.append(types.Content(role="user", parts=parts))
        else:
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=message)],
                )
            )

        # Configurar tools
        tools = []
        for tool_group in self.tools_config.get("tools", []):
            for fd in tool_group.get("function_declarations", []):
                tools.append(
                    types.Tool(
                        function_declarations=[
                            types.FunctionDeclaration(
                                name=fd["name"],
                                description=fd["description"],
                                parameters=fd.get("parameters"),
                            )
                        ]
                    )
                )

        # Llamar al modelo
        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=tools,
                temperature=0.3,
                max_output_tokens=2048,
            ),
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Parsear respuesta
        result = {
            "model": model,
            "latency_ms": latency_ms,
            "function_calls": [],
            "text": None,
        }

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.function_call:
                    result["function_calls"].append({
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args) if part.function_call.args else {},
                    })
                elif part.text:
                    result["text"] = part.text

        logger.info(
            "llm_call",
            model=model,
            latency_ms=latency_ms,
            has_function_calls=len(result["function_calls"]) > 0,
            has_text=result["text"] is not None,
        )

        return result
