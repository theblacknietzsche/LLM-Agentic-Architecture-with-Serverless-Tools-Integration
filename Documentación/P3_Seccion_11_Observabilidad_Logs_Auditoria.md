# PROYECTO 3 – Sección 11: Observabilidad, Logs y Auditoría

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 11.1 Stack de Observabilidad

| Capa | Herramienta GCP | Función |
|---|---|---|
| **Logs estructurados** | Cloud Logging | Registrar eventos del agente, tools, workflows y errores |
| **Trazabilidad distribuida** | Cloud Trace | Medir latencia end-to-end y por componente |
| **Métricas y alertas** | Cloud Monitoring | Dashboards de KPIs, alertas automáticas |

```
┌────────────────────────────────────────────────────────────────┐
│                    OBSERVABILIDAD                               │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  CLOUD LOGGING    │  │ CLOUD TRACE  │  │ CLOUD MONITORING │ │
│  │                   │  │              │  │                  │ │
│  │ · Logs del agente │  │ · Trace por  │  │ · Dashboards     │ │
│  │ · Logs de tools   │  │   request    │  │ · Alertas        │ │
│  │ · Logs de errors  │  │ · Spans por  │  │ · SLOs           │ │
│  │ · Logs de workflow│  │   componente │  │                  │ │
│  └────────┬─────────┘  └──────┬───────┘  └────────┬─────────┘ │
│           │                   │                    │            │
│           ▼                   ▼                    ▼            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    FUENTES DE DATOS                      │   │
│  │                                                          │   │
│  │  API Gateway  ·  Orchestrator  ·  Tools (×4)  · Workflows│   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

## 11.2 Logs del Agente (Orchestrator)

Cada consulta al agente genera un log estructurado que captura el ciclo ReAct completo.

### Estructura del log por request

```json
{
  "severity": "INFO",
  "timestamp": "2026-06-15T14:30:05.123Z",
  "log_type": "agent_request",
  "request_id": "req-20260615-abc123",
  "user_id": "user-francisco",
  "trace_id": "projects/brewfinance/traces/a1b2c3d4e5f6",
  "input": {
    "message": "¿Cuál es mi sabor más rentable?",
    "message_tokens": 12,
    "history_turns": 2,
    "history_tokens": 180
  },
  "context": {
    "system_prompt_tokens": 400,
    "tool_declarations_tokens": 400,
    "total_input_tokens": 992
  },
  "react_trace": {
    "total_steps": 3,
    "model_used": "gemini-2.5-flash",
    "fallback_triggered": false,
    "steps": [
      {
        "step": 1,
        "type": "thought_action",
        "thought": "Necesito ventas y costos del mes actual",
        "action": {
          "tool": "sheets_reader",
          "params": {"hoja": "Ventas", "filtros": {"mes": "2026-06"}},
          "latency_ms": 342,
          "status": "success",
          "response_tokens": 85
        }
      },
      {
        "step": 2,
        "type": "thought_action",
        "thought": "Ahora necesito los costos de producción",
        "action": {
          "tool": "sheets_reader",
          "params": {"hoja": "Costos"},
          "latency_ms": 298,
          "status": "success",
          "response_tokens": 60
        }
      },
      {
        "step": 3,
        "type": "thought_action",
        "thought": "Calculo márgenes con los datos obtenidos",
        "action": {
          "tool": "calculator",
          "params": {"operacion": "margen_por_sabor"},
          "latency_ms": 45,
          "status": "success",
          "response_tokens": 120
        }
      }
    ]
  },
  "output": {
    "answer": "Tu sabor más rentable este mes es mango con un margen bruto del 61.1%...",
    "answer_tokens": 85,
    "total_output_tokens": 550
  },
  "performance": {
    "total_latency_ms": 4230,
    "llm_latency_ms": 2850,
    "tool_latency_ms": 685,
    "overhead_ms": 695,
    "total_tokens_in": 992,
    "total_tokens_out": 550
  },
  "guardrails": {
    "validations_run": 3,
    "validations_passed": 3,
    "validations_failed": 0
  }
}
```

### Tipos de log del agente

| Log type | Severity | Cuándo se emite |
|---|---|---|
| `agent_request` | INFO | Al completar cada consulta (log completo del ciclo) |
| `agent_fallback` | WARNING | Cuando se escala de Flash a Pro |
| `agent_max_steps` | WARNING | Cuando se alcanza el límite de 5 pasos ReAct |
| `agent_error` | ERROR | Cuando el agente no puede completar la consulta |
| `guardrail_rejected` | WARNING | Cuando un tool call es rechazado por el guardrail |

---

## 11.3 Logs de Tools (Cloud Functions)

Cada tool emite su propio log estructurado al ejecutarse.

### Estructura del log por tool call

```json
{
  "severity": "INFO",
  "timestamp": "2026-06-15T14:30:05.465Z",
  "log_type": "tool_execution",
  "request_id": "req-20260615-abc123",
  "trace_id": "projects/brewfinance/traces/a1b2c3d4e5f6",
  "tool": {
    "name": "sheets_reader",
    "function_name": "bf-sheets-reader",
    "invocation_id": "inv-789xyz"
  },
  "input": {
    "hoja": "Ventas",
    "filtros": {"mes": "2026-06"},
    "campos": null
  },
  "output": {
    "status": "success",
    "total_registros": 12,
    "response_size_bytes": 2048
  },
  "performance": {
    "total_latency_ms": 342,
    "sheets_api_latency_ms": 280,
    "processing_latency_ms": 62,
    "cold_start": false
  },
  "errors": null
}
```

### Log de tool con error

```json
{
  "severity": "ERROR",
  "timestamp": "2026-06-15T14:30:05.465Z",
  "log_type": "tool_execution",
  "request_id": "req-20260615-def456",
  "tool": {
    "name": "sheets_writer",
    "function_name": "bf-sheets-writer"
  },
  "input": {
    "hoja": "Ventas",
    "registro": {"sabor": "uva", "cantidad": 5}
  },
  "output": {
    "status": "error",
    "error_code": "UNKNOWN_SABOR",
    "message": "Sabor 'uva' no reconocido. Válidos: mango, fresa, limon, jengibre, menta."
  },
  "performance": {
    "total_latency_ms": 15,
    "cold_start": false
  }
}
```

### Tipos de log de tools

| Log type | Severity | Cuándo se emite |
|---|---|---|
| `tool_execution` (success) | INFO | Cada ejecución exitosa de un tool |
| `tool_execution` (error) | ERROR | Cada ejecución fallida (error de negocio o técnico) |
| `tool_cold_start` | INFO | Cuando una Cloud Function arranca desde cero |
| `tool_retry` | WARNING | Cuando un tool es reintentado (por workflow o agente) |
| `tool_idempotency_hit` | INFO | Cuando sheets_writer detecta un duplicado |

---

## 11.4 Latencias por Tool

### Métricas de latencia recopiladas

Cada tool call registra 3 métricas de latencia en Cloud Trace:

```
┌──────────────────── total_latency_ms ────────────────────────┐
│                                                               │
│  ┌─ cold_start_ms ─┐  ┌─ external_api_ms ─┐  ┌─ process_ms ─┐
│  │ (solo si aplica) │  │ (Sheets API /     │  │ (lógica     │ │
│  │                  │  │  Vertex AI)       │  │  interna)   │ │
│  └──────────────────┘  └──────────────────┘  └─────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Latencias esperadas por tool

| Tool | P50 | P90 | P99 | Componente dominante |
|---|---|---|---|---|
| `sheets_reader` | 300ms | 500ms | 800ms | Sheets API (lectura) |
| `sheets_writer` | 400ms | 600ms | 1,000ms | Sheets API (escritura + idempotency check) |
| `calculator` | 30ms | 50ms | 100ms | Cómputo local (sin API externa) |
| `report_generator` | 50ms | 80ms | 150ms | Cómputo local (formateo de texto) |

### Latencia del LLM (Gemini)

| Modelo | P50 | P90 | P99 |
|---|---|---|---|
| Gemini 2.5 Flash | 600ms | 1,000ms | 1,800ms |
| Gemini 2.5 Pro | 1,200ms | 2,500ms | 4,000ms |

### Latencia end-to-end por tipo de consulta

| Tipo | Pasos | LLM calls | Tool calls | P50 total | P90 total |
|---|---|---|---|---|---|
| Simple (registro) | 1 | 1 | 1 | 1.5s | 2.5s |
| Directa (consulta) | 1 | 1 | 1 | 1.5s | 2.5s |
| Análisis (margen) | 3 | 3 | 3 | 4.0s | 6.5s |
| Complejo (recomendación) | 4 | 4 | 4 | 5.5s | 9.0s |

---

## 11.5 Tool-Call Success Rate

### Cómo se calcula

```
Tool-Call Success Rate = (tool calls con status "success") / (total tool calls) × 100
```

### Dashboard de métricas

| Métrica | Fórmula | Fuente | Meta (KPI) |
|---|---|---|---|
| **Tool-Call Success Rate (global)** | success / total × 100 | Cloud Logging: filtro `log_type=tool_execution` | ≥ 95% |
| **Success rate por tool** | success por tool / total por tool × 100 | Cloud Logging: filtro por `tool.name` | ≥ 95% cada uno |
| **Error rate por código** | conteo por `error_code` / total × 100 | Cloud Logging: filtro por `output.error_code` | < 5% |
| **Cold start rate** | cold_start=true / total × 100 | Cloud Logging: filtro `performance.cold_start` | < 20% |

### Queries de Cloud Logging para métricas

**Tool-Call Success Rate global (últimas 24h):**

```
resource.type="cloud_function"
jsonPayload.log_type="tool_execution"
timestamp >= "2026-06-15T00:00:00Z"
```

Agrupar por `jsonPayload.output.status` → calcular `success / total × 100`.

**Latencia P90 por tool (última semana):**

```
resource.type="cloud_function"
jsonPayload.log_type="tool_execution"
jsonPayload.output.status="success"
timestamp >= "2026-06-08T00:00:00Z"
```

Agrupar por `jsonPayload.tool.name` → percentil 90 de `jsonPayload.performance.total_latency_ms`.

**Errores más frecuentes:**

```
resource.type="cloud_function"
jsonPayload.log_type="tool_execution"
jsonPayload.output.status="error"
```

Agrupar por `jsonPayload.output.error_code` → ordenar por conteo descendente.

---

## 11.6 Trazabilidad Completa

### Trace distribuido con Cloud Trace

Cada request del usuario genera un **trace** único que conecta todos los componentes involucrados.

```
TRACE: a1b2c3d4e5f6
│
├── SPAN: api_gateway (50ms)
│   └── Validación de auth + rate limit
│
├── SPAN: orchestrator (4,230ms)
│   │
│   ├── SPAN: llm_call_1 (850ms)
│   │   ├── model: gemini-2.5-flash
│   │   ├── input_tokens: 992
│   │   ├── output: function_call(sheets_reader)
│   │   └── output_tokens: 120
│   │
│   ├── SPAN: tool_call_1 (342ms)
│   │   ├── tool: sheets_reader
│   │   ├── params: {hoja: "Ventas", filtros: {mes: "2026-06"}}
│   │   ├── status: success
│   │   └── registros: 12
│   │
│   ├── SPAN: llm_call_2 (780ms)
│   │   ├── model: gemini-2.5-flash
│   │   ├── output: function_call(sheets_reader)
│   │   └── output_tokens: 95
│   │
│   ├── SPAN: tool_call_2 (298ms)
│   │   ├── tool: sheets_reader
│   │   ├── params: {hoja: "Costos"}
│   │   └── status: success
│   │
│   ├── SPAN: guardrail_check (5ms)
│   │   └── validation: passed
│   │
│   ├── SPAN: llm_call_3 (720ms)
│   │   ├── model: gemini-2.5-flash
│   │   ├── output: function_call(calculator)
│   │   └── output_tokens: 110
│   │
│   ├── SPAN: tool_call_3 (45ms)
│   │   ├── tool: calculator
│   │   ├── params: {operacion: "margen_por_sabor"}
│   │   └── status: success
│   │
│   └── SPAN: llm_call_4 (500ms)
│       ├── model: gemini-2.5-flash
│       ├── output: answer (texto final)
│       └── output_tokens: 85
│
└── TOTAL: 4,280ms
```

### Implementación del tracing en Python

```python
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configuración
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(CloudTraceSpanExporter())
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("brewfinance-orchestrator")

async def handle_chat(message: str, request_id: str):
    with tracer.start_as_current_span("orchestrator") as span:
        span.set_attribute("request_id", request_id)
        span.set_attribute("user_message_length", len(message))

        # Ciclo ReAct
        for step in range(MAX_REACT_STEPS):
            with tracer.start_as_current_span(f"llm_call_{step+1}") as llm_span:
                llm_span.set_attribute("model", current_model)
                response = await gemini.generate(context)
                llm_span.set_attribute("output_tokens", response.token_count)

            if response.has_function_call():
                with tracer.start_as_current_span(f"tool_call_{step+1}") as tool_span:
                    tool_span.set_attribute("tool", response.function_call.name)
                    result = await execute_tool(response.function_call)
                    tool_span.set_attribute("status", result.status)
                    tool_span.set_attribute("latency_ms", result.latency_ms)
            else:
                span.set_attribute("total_steps", step + 1)
                return response.text
```

---

## 11.7 Alertas de Cloud Monitoring

| Alerta | Condición | Severidad | Canal de notificación |
|---|---|---|---|
| **Tool-call success rate bajo** | Success rate < 90% en ventana de 1 hora | Critical | Email al admin |
| **Latencia alta** | P90 > 20s en ventana de 15 min | Warning | Email al admin |
| **Errores de autenticación** | Cualquier `AUTH_ERROR` en tools | Critical | Email inmediato |
| **Agente alcanzó max steps** | > 5 eventos `agent_max_steps` en 1 hora | Warning | Email al admin |
| **Workflow fallido** | Cualquier workflow en estado `FAILED` | Critical | Email al admin |
| **Cold start excesivo** | Cold start rate > 50% en 1 hora | Warning | Email al admin |

---

## 11.8 Auditoría

### Datos auditables por consulta

Cada request al agente produce un registro de auditoría completo que permite reconstruir exactamente qué pasó:

| Dato | Fuente | Propósito de auditoría |
|---|---|---|
| Quién preguntó | `user_id` en log del agente | Identificar el usuario |
| Qué preguntó | `input.message` en log del agente | Pregunta original completa |
| Qué razonó el agente | `react_trace.steps[].thought` | Justificación de cada decisión |
| Qué tools llamó | `react_trace.steps[].action.tool` + `.params` | Acciones ejecutadas con parámetros |
| Qué datos obtuvo | `tool_execution` logs | Datos leídos de Sheets |
| Qué escribió | `sheets_writer` logs con `registro` | Datos modificados en Sheets |
| Qué respondió | `output.answer` | Respuesta entregada al usuario |
| Cuánto costó | `performance.total_tokens_*` | Tokens consumidos |
| Cuánto tardó | `performance.total_latency_ms` | Latencia total |

### Retención de logs

| Tipo de log | Retención | Justificación |
|---|---|---|
| Logs del agente (`agent_request`) | 90 días | Suficiente para análisis de tendencias y debugging |
| Logs de tools (`tool_execution`) | 30 días | Volumen más alto, datos operativos |
| Logs de errores (severity ERROR) | 180 días | Retención extendida para investigación |
| Traces (Cloud Trace) | 30 días | Default de GCP, suficiente para performance tuning |
