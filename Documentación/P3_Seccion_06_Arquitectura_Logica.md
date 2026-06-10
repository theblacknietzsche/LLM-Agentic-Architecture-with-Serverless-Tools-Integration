# PROYECTO 3 – Sección 6: Arquitectura Lógica del Sistema de Agentes

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 6.1 Diagrama de Arquitectura Completa

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   ┌───────────────────┐                                                                 │
│   │     USUARIO        │                                                                │
│   │  (Chat / texto)    │                                                                │
│   └─────────┬─────────┘                                                                 │
│             │ HTTPS (texto libre en español)                                            │
│             ▼                                                                           │
│   ┌───────────────────────────────────────────────────────┐                              │
│   │              INTERFAZ / API GATEWAY                    │                             │
│   │          (Cloud Functions 2nd gen — HTTP)              │                             │
│   │                                                        │                            │
│   │  · Autenticación (API Key via header)                  │                             │
│   │  · Rate limiting (max 10 req/min por usuario)          │                             │
│   │  · Validación de input (longitud, encoding)            │                             │
│   │  · Ruteo al orchestrator                               │                             │
│   └─────────────────────┬─────────────────────────────────┘                              │
│                         │ HTTP interno                                                   │
│                         ▼                                                                │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│   │                      BACKEND ORCHESTRATOR                                        │   │
│   │                   (Cloud Run — FastAPI container)                                 │   │
│   │                                                                                  │   │
│   │  ┌─────────────────────────────────────────────────────────────────────────┐     │   │
│   │  │                     CICLO ReAct                                         │     │   │
│   │  │                                                                         │     │   │
│   │  │   ┌───────────┐    ┌───────────┐    ┌─────────────┐    ┌──────────┐   │     │   │
│   │  │   │  THOUGHT   │───►│  ACTION    │───►│ OBSERVATION  │───►│ ¿Listo?  │   │     │   │
│   │  │   │ (razonar)  │    │ (tool call)│    │ (resultado)  │    │          │   │     │   │
│   │  │   └───────────┘    └───────────┘    └─────────────┘    └────┬─────┘   │     │   │
│   │  │        ▲                                                     │ NO      │     │   │
│   │  │        └─────────────────────────────────────────────────────┘         │     │   │
│   │  │                                                              │ SÍ      │     │   │
│   │  │                                                              ▼         │     │   │
│   │  │                                                        ┌──────────┐   │     │   │
│   │  │                                                        │  ANSWER  │   │     │   │
│   │  │                                                        └──────────┘   │     │   │
│   │  └─────────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                  │   │
│   │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐               │   │
│   │  │  Context Manager  │  │    Guardrails     │  │  Session Memory  │               │   │
│   │  │ (system prompt +  │  │ (validación pre-  │  │ (historial 5     │               │   │
│   │  │  tool schemas +   │  │  ejecución de     │  │  turnos en       │               │   │
│   │  │  historial)       │  │  tool calls)      │  │  context window) │               │   │
│   │  └──────────────────┘  └──────────────────┘  └──────────────────┘               │   │
│   └──────┬──────────────────────┬───────────────────────────────────────┬────────────┘   │
│          │                      │                                       │                │
│          │ Gemini API           │ HTTP (tool calls)                     │ HTTP (logs)    │
│          ▼                      ▼                                       ▼                │
│   ┌──────────────┐   ┌──────────────────────────────────────────┐  ┌─────────────────┐  │
│   │ LLM PROVIDER │   │         TOOLS SERVERLESS                  │  │ LOGGING +       │  │
│   │              │   │      (Cloud Functions 2nd gen)            │  │ MONITORING      │  │
│   │ ┌──────────┐ │   │                                           │  │                 │  │
│   │ │ Gemini   │ │   │  ┌──────────┐  ┌──────────┐              │  │ ┌─────────────┐ │  │
│   │ │ 2.5      │ │   │  │ sheets   │  │ sheets   │              │  │ │ Cloud       │ │  │
│   │ │ Flash    │ │   │  │ _reader  │  │ _writer  │              │  │ │ Logging     │ │  │
│   │ │ (90%)    │ │   │  └─────┬────┘  └─────┬────┘              │  │ └─────────────┘ │  │
│   │ └──────────┘ │   │        │              │                   │  │ ┌─────────────┐ │  │
│   │ ┌──────────┐ │   │        ▼              ▼                   │  │ │ Cloud       │ │  │
│   │ │ Gemini   │ │   │  ┌───────────────────────┐               │  │ │ Trace       │ │  │
│   │ │ 2.5      │ │   │  │    GOOGLE SHEETS      │               │  │ └─────────────┘ │  │
│   │ │ Pro      │ │   │  │    (Data Store)        │               │  │ ┌─────────────┐ │  │
│   │ │ (10%)    │ │   │  │   · Ventas             │               │  │ │ Cloud       │ │  │
│   │ └──────────┘ │   │  │   · Costos             │               │  │ │ Monitoring  │ │  │
│   └──────────────┘   │  │   · Gastos             │               │  │ └─────────────┘ │  │
│                      │  └───────────────────────┘               │  └─────────────────┘  │
│                      │                                           │                       │
│                      │  ┌──────────┐  ┌──────────┐              │                       │
│                      │  │calculator│  │ report   │              │                       │
│                      │  │          │  │_generator│              │                       │
│                      │  └──────────┘  └──────────┘              │                       │
│                      └──────────────────────────────────────────┘                       │
│                                          │                                               │
│                                          │ Triggers (multi-paso)                         │
│                                          ▼                                               │
│                      ┌──────────────────────────────────────────┐                       │
│                      │       WORKFLOW ORCHESTRATOR               │                       │
│                      │       (Google Workflows)                  │                       │
│                      │                                           │                       │
│                      │  · Resumen mensual automático             │                       │
│                      │  · Alerta de margen bajo                  │                       │
│                      │  · Reporte semanal programado             │                       │
│                      └──────────────────────────────────────────┘                       │
│                                                                                         │
│                              GOOGLE CLOUD PLATFORM                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6.2 Descripción de Cada Componente

### Componente 1: Interfaz / API Gateway

| Atributo | Valor |
|---|---|
| **Implementación** | Cloud Function 2nd gen (HTTP trigger) |
| **Responsabilidad** | Punto de entrada único al sistema. Recibe el mensaje del usuario, valida autenticación y formato, y reenvía al orchestrator |
| **Autenticación** | API Key en header `X-API-Key` — validada contra Secret Manager |
| **Rate limiting** | 10 requests/minuto por API Key (suficiente para 3 usuarios con uso normal) |
| **Validación** | Mensaje no vacío, longitud ≤ 2,000 caracteres, encoding UTF-8 |
| **Protocolo** | HTTPS (entrada) → HTTP interno (hacia Cloud Run) |

### Componente 2: Backend Orchestrator

| Atributo | Valor |
|---|---|
| **Implementación** | Cloud Run (contenedor Docker con FastAPI) |
| **Responsabilidad** | Núcleo del sistema. Ejecuta el ciclo ReAct: recibe el mensaje, construye el contexto, invoca al LLM, despacha tool calls, recolecta resultados y genera la respuesta final |
| **Subcomponentes** | Context Manager, Guardrails, Session Memory |
| **Endpoints** | `POST /chat` (mensaje del usuario), `GET /health` (health check) |
| **Escalado** | min-instances=0, max-instances=3 (escala a cero cuando no hay tráfico) |

#### Subcomponente: Context Manager
Construye el context window para cada invocación al LLM. Ensambla: system prompt (~400 tokens) + tool declarations (~400 tokens) + historial de sesión (variable) + mensaje actual (~50 tokens).

#### Subcomponente: Guardrails
Intercepta los `function_call` que el LLM emite y valida parámetros antes de ejecutar el tool (rangos de precio, sabores válidos, canales válidos). Si la validación falla, retorna un error al LLM para que corrija.

#### Subcomponente: Session Memory
Mantiene los últimos 5 turnos de conversación en memoria (in-context). No persiste entre sesiones. Permite al agente resolver referencias como "ese sabor" o "compáralo con el anterior".

### Componente 3: LLM Provider

| Atributo | Valor |
|---|---|
| **Implementación** | Google Vertex AI API (Gemini) |
| **Modelo principal** | Gemini 2.5 Flash — 90% de consultas |
| **Modelo fallback** | Gemini 2.5 Pro — 10% de consultas (razonamiento complejo) |
| **Protocolo** | HTTPS (Vertex AI API / `generateContent`) |
| **Function calling** | Nativo via `function_declarations` en parámetro `tools` |
| **Región** | `us-central1` (endpoint global) |

### Componente 4: Tools Serverless

| Atributo | Valor |
|---|---|
| **Implementación** | 4 Cloud Functions 2nd gen (HTTP trigger) |
| **Tools** | `sheets_reader`, `sheets_writer`, `calculator`, `report_generator` |
| **Protocolo** | HTTP (invocadas por el orchestrator durante el ciclo ReAct) |
| **Autenticación interna** | Service account con permisos mínimos (invoker role) |
| **Data store** | Google Sheets (hojas: Ventas, Costos, Gastos) |
| **Detalle completo** | Ver Sección 5 (contratos JSON, errores, idempotencia) |

### Componente 5: Workflow Orchestrator

| Atributo | Valor |
|---|---|
| **Implementación** | Google Workflows |
| **Responsabilidad** | Ejecutar flujos multi-paso que el agente dispara o que corren de forma programada |
| **Workflows definidos** | 3 (ver sección 6.4) |
| **Trigger** | HTTP (invocado por el orchestrator) o Cloud Scheduler (programado) |
| **Detalle completo** | Ver Sección 8 |

### Componente 6: Logging + Monitoring

| Atributo | Valor |
|---|---|
| **Implementación** | Cloud Logging + Cloud Trace + Cloud Monitoring |
| **Cloud Logging** | Logs estructurados de cada componente: requests del usuario, ciclos ReAct (thought/action/observation), tool calls (input/output/latencia), errores |
| **Cloud Trace** | Trazabilidad distribuida de latencia: request → orchestrator → LLM → tool → response. Permite identificar cuellos de botella |
| **Cloud Monitoring** | Dashboards y alertas: task success rate, tool-call success rate, latencia P50/P95, errores por tipo |
| **Detalle completo** | Ver Sección 11 |

---

## 6.3 Flujo de Datos Completo

### Flujo principal: Usuario → Agente → LLM → Tool(s) → LLM → Usuario

```
PASO  COMPONENTE                ACCIÓN                                  DATOS
────  ─────────────────────     ──────────────────────────────────      ─────────────────────
 1    Usuario                   Envía mensaje                          "¿Cuál es mi margen
                                                                        por sabor este mes?"

 2    API Gateway               Valida auth + rate limit               API Key ✓, rate ✓
      (Cloud Function)          Reenvía al orchestrator                POST /chat

 3    Orchestrator              Context Manager ensambla contexto      system_prompt +
      (Cloud Run)               (system prompt + tools + historial)    tool_schemas +
                                                                       historial + mensaje

 4    Orchestrator              Envía contexto al LLM                  generateContent()
      → LLM Provider

 5    LLM (Gemini Flash)        THOUGHT: "Necesito ventas y costos"    Razonamiento interno
                                ACTION: function_call                   sheets_reader
                                                                        {hoja: "Ventas",
                                                                         filtros: {mes: "06"}}

 6    Orchestrator              Guardrail valida parámetros            ✓ hoja válida
      → Guardrails              Despacha tool call                     ✓ filtros válidos

 7    Tool: sheets_reader       Lee datos de Google Sheets             GET Sheets API
      (Cloud Function)          Retorna JSON                           [{sabor, qty, precio}]

 8    Orchestrator              LOG: tool call exitoso                 → Cloud Logging
      → Logging                 TRACE: latencia del tool               → Cloud Trace

 9    Orchestrator              OBSERVATION: datos de ventas           JSON con ventas
      → LLM Provider            Envía resultado al LLM                del mes

10    LLM (Gemini Flash)        THOUGHT: "Ahora necesito costos"      Razonamiento interno
                                ACTION: function_call                   sheets_reader
                                                                        {hoja: "Costos"}

11    Pasos 6-9 se repiten      (lectura de costos)                    [{sabor, costo}]

12    LLM (Gemini Flash)        THOUGHT: "Tengo ambos, calculo"       Razonamiento interno
                                ACTION: function_call                   calculator
                                                                        {op: "margen_por_sabor",
                                                                         params: {ventas, costos}}

13    Pasos 6-9 se repiten      (cálculo de márgenes)                  [{sabor, margen%}]

14    LLM (Gemini Flash)        THOUGHT: "Tengo todo para responder"  Razonamiento interno
                                ANSWER: respuesta final                Texto conversacional

15    Orchestrator              LOG: trace completo del ciclo          → Cloud Logging
      → Logging                 (3 pasos, 3 tool calls, latencia)     → Cloud Trace

16    API Gateway               Retorna respuesta al usuario           HTTP 200 + JSON
      → Usuario

17    Usuario                   Recibe respuesta                       "Tu sabor más rentable
                                                                        es mango con 61.1%..."
```

### Flujo de escritura (con workflow): Usuario → Agente → Tool → Workflow → Usuario

```
PASO  COMPONENTE                ACCIÓN                                  DATOS
────  ─────────────────────     ──────────────────────────────────      ─────────────────────
 1    Usuario                   "Registra que vendí 10 de fresa        Texto libre
                                 a $45 en el gimnasio"

 2    API Gateway → Orchestrator → LLM                                 (pasos 2-5 del flujo
                                                                        principal)

 3    LLM (Gemini Flash)        THOUGHT: "Es un registro de venta"     Razonamiento
                                ACTION: function_call                   sheets_writer
                                {hoja: "Ventas", registro: {sabor:
                                "fresa", cantidad: 10, precio: 45,
                                canal: "gimnasio", fecha: "2026-06-15"},
                                idempotency_key: "v-20260615-fresa-10"}

 4    Guardrails                Valida: cantidad ✓, precio ✓,          Validación OK
                                sabor ✓, canal ✓, fecha ✓

 5    Tool: sheets_writer       Inserta fila en Google Sheets          Fila 48 insertada
      (Cloud Function)          Retorna confirmación                   {status: "success"}

 6    Orchestrator              ¿Trigger de workflow?                  Sí: nueva venta
      → Workflow Orchestrator   Dispara workflow de verificación       registrada

 7    Google Workflows          Paso 1: Leer ventas del mes            sheets_reader
                                Paso 2: Calcular acumulado             calculator
                                Paso 3: ¿Margen bajo en algún sabor?  Evaluar
                                (si margen < 40% → generar alerta)

 8    LLM (Gemini Flash)        ANSWER: confirmación + contexto        Texto conversacional

 9    Usuario                   "Listo, registré 10 de fresa 345ml     Respuesta
                                 a $45 en gimnasio. Tu acumulado de
                                 fresa este mes: 28 unidades, margen
                                 57.8% — todo dentro de rango normal."
```

---

## 6.4 Workflows del Sistema

El Workflow Orchestrator (Google Workflows) ejecuta 3 flujos multi-paso:

| # | Workflow | Trigger | Pasos | Propósito |
|---|---|---|---|---|
| WF1 | `post_write_check` | HTTP (disparado por orchestrator tras cada `sheets_writer`) | 3 | Verificar acumulados tras cada registro: leer ventas del mes → calcular margen actualizado → evaluar si hay alertas |
| WF2 | `weekly_summary` | Cloud Scheduler (todos los lunes a las 9:00 AM) | 4 | Generar resumen semanal: leer ventas → leer gastos → calcular métricas → almacenar reporte en Sheets |
| WF3 | `low_margin_alert` | Condicional (disparado por WF1 si margen < 40%) | 2 | Generar alerta: construir mensaje de advertencia → enviar notificación al usuario |

El detalle completo de estos workflows (diagrama, manejo de errores, reintentos) se desarrolla en la Sección 8.

---

## 6.5 Comunicación entre Componentes

| Origen | Destino | Protocolo | Autenticación | Latencia esperada |
|---|---|---|---|---|
| Usuario → API Gateway | HTTPS | API Key (header) | < 50ms |
| API Gateway → Orchestrator | HTTP interno (Cloud Run) | IAM (service account) | < 30ms |
| Orchestrator → LLM (Gemini) | HTTPS (Vertex AI API) | Service account + OAuth | 500ms - 2s por llamada |
| Orchestrator → Tools | HTTP (Cloud Functions) | IAM (invoker role) | 100ms - 500ms por tool |
| Tools → Google Sheets | HTTPS (Sheets API) | Service account | 200ms - 400ms |
| Orchestrator → Workflows | HTTPS (Workflows API) | IAM (invoker role) | 100ms (trigger async) |
| Todos → Cloud Logging | gRPC (SDK nativo) | Automático (GCP) | < 10ms (async) |

### Latencia total estimada por tipo de consulta

| Tipo de consulta | Pasos ReAct | Llamadas al LLM | Tool calls | Latencia total estimada |
|---|---|---|---|---|
| Registro simple | 1 | 1 | 1 (writer) | ~2-3s |
| Consulta directa | 1 | 1 | 1 (reader) | ~2-3s |
| Análisis de margen | 3 | 3 | 3 (reader + reader + calc) | ~5-7s |
| Recomendación completa | 4 | 4 | 4 (reader + reader + calc + report) | ~8-12s |
| Resumen mensual | 4 | 4 | 4 (reader + reader + calc + report) | ~8-12s |

Todas las estimaciones caen dentro de los KPIs definidos en la Sección 1 (< 8s simple, < 20s complejo).
