# PROYECTO 3 – Sección 12: Documentación Final Profesional

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco  
**Versión:** 1.0.0  
**Fecha:** Junio 2026

---

## 1. Caso de Uso

### Escenario

Microempresa de bebidas embotelladas artesanales con 3 meses de operación en México. Produce 5 sabores (mango, fresa, limón, jengibre, menta) en 2 presentaciones (345ml, 1L), comercializados a través de un gimnasio de escalada y venta directa por redes sociales. Volumen mensual: ~40 unidades de 345ml y ~3 unidades de 1L.

### Problema

Las decisiones de pricing, producción y distribución se toman de forma intuitiva. Los datos existen en Google Sheets pero no se analizan sistemáticamente: no hay visibilidad sobre márgenes reales por sabor ni por canal, no se proyecta demanda, y no se evalúa qué combinación de productos maximiza la rentabilidad.

### Solución

**BrewFinance Agent** — Agente conversacional que se conecta a los Google Sheets del negocio, analiza datos financieros, genera recomendaciones accionables y registra información nueva, todo a través de lenguaje natural en español.

### Usuarios

| Usuario | Rol | Necesidad principal |
|---|---|---|
| Fundador | Decisor estratégico | Márgenes, pricing, proyecciones |
| Socio de producción | Operaciones | Costos, volúmenes óptimos |
| Socio de ventas | Comercialización | Tendencias por canal, registros |

Perfil técnico: no técnicos. Interfaz: chat en texto libre, español.

### KPIs

| KPI | Meta | Método de medición |
|---|---|---|
| Task Success Rate | ≥ 85% | Evaluación manual sobre 20 consultas de prueba |
| Tool-Call Success Rate | ≥ 95% | Logs del agente (status por tool call) |
| Latencia de resolución | < 8s simple, < 20s complejo | Timestamps en pipeline |
| Pasos promedio por tarea | ≤ 3 | Conteo de tool calls en trace |
| Error Handling Rate | ≥ 90% | 15 escenarios de fallo inducidos |

Detalle completo: Sección 1.

---

## 2. Modelo

### Selección

| Decisión | Valor |
|---|---|
| Modelo principal | Gemini 2.5 Flash (Vertex AI) |
| Modelo fallback | Gemini 2.5 Pro (Vertex AI) |
| Estrategia | Small-first: Flash para 90% de consultas, Pro para 10% complejas |

### Justificación

| Factor | Justificación |
|---|---|
| Razonamiento | Flash incluye "thinking" configurable, suficiente para análisis financiero de microempresa. Pro como fallback para recomendaciones multi-variable. |
| Costo | Flash: $0.30/$2.50 por millón de tokens (input/output). A ~100 consultas/mes, costo de inferencia ≈ $0.18 USD/mes. |
| Tool-calling | Soporte nativo vía `function_declarations`. 4 herramientas registradas sin necesidad de prompting manual. |
| Latencia | Flash: 500ms-1s por llamada. En ciclo ReAct de 3 pasos: 4-7s total (dentro de KPIs). |
| Ecosistema | El negocio opera sobre Google Sheets. Vertex AI permite integración nativa con Sheets API, Cloud Functions, Cloud Logging e IAM. |

### Comparativa evaluada

| Modelo | Costo/1M input | Costo/1M output | Tool-calling | Seleccionado |
|---|---|---|---|---|
| Gemini 2.5 Flash | $0.30 | $2.50 | Nativo | **Sí (principal)** |
| Gemini 2.5 Pro | $1.25 | $10.00 | Nativo | **Sí (fallback)** |
| GPT-4o mini | $0.15 | $0.60 | Nativo | No (ecosistema cross-cloud) |
| Claude 3.5 Haiku | $0.80 | $4.00 | Nativo | No (ecosistema cross-cloud) |

Detalle completo: Sección 2.

---

## 3. Patrón Agentic

### Patrón principal: ReAct (Reason + Act) + Tool-Calling

El agente alterna entre pasos de razonamiento (Thought) y acción (Action), observando resultados antes de decidir el siguiente paso. Gemini selecciona qué tool invocar de forma autónoma mediante function calling nativo.

### Ciclo ReAct

```
Usuario (pregunta)
    │
    ▼
THOUGHT → ¿Qué datos necesito?
    │
    ▼
ACTION → function_call(tool, params)
    │
    ▼
OBSERVATION → Resultado del tool
    │
    ├── ¿Necesito más datos? → SÍ → volver a THOUGHT
    │
    └── NO → ANSWER (respuesta al usuario)
```

### Patrones complementarios

| Patrón | Propósito | Implementación |
|---|---|---|
| **Guardrail** | Validar tool calls antes de ejecutarlos | Reglas de negocio: sabores válidos, rangos de precio, hojas escribibles. Si falla, rechaza y pide corrección al LLM. |
| **Memory (sesión)** | Coherencia multi-turno | Últimos 5 turnos en context window. Permite resolver "ese sabor", "compáralo con el anterior". No persiste entre sesiones. |

### Trade-offs

| Ventaja | Desventaja | Mitigación |
|---|---|---|
| Flexibilidad (se adapta a cualquier tarea) | Latencia acumulada por paso | Gemini Flash optimizado para baja latencia |
| Trace auditable completo | Costo proporcional a pasos | Estrategia small-first (Flash 90%, Pro 10%) |
| Agregar tools sin reentrenamiento | Riesgo de loops infinitos | Límite hard de 5 iteraciones |
| Sin paralelismo nativo | Ejecución secuencial de tools | Gemini soporta `parallel_tool_calls` para fase posterior |

Detalle completo: Sección 3.

---

## 4. Arquitectura

### Componentes del sistema

```
USUARIO (Chat/texto)
    │
    ▼
API GATEWAY (Cloud Function) ── auth + rate limit
    │
    ▼
ORCHESTRATOR (Cloud Run / FastAPI) ── ReAct loop + Guardrails + Session Memory
    │
    ├──► GEMINI 2.5 FLASH / PRO (Vertex AI)
    │
    ├──► TOOL: sheets_reader (Cloud Function) ──► Google Sheets
    ├──► TOOL: sheets_writer (Cloud Function) ──► Google Sheets
    ├──► TOOL: calculator (Cloud Function)
    ├──► TOOL: report_generator (Cloud Function)
    │
    ├──► WORKFLOWS (Google Workflows)
    │     ├── post_write_check (tras cada registro)
    │     ├── weekly_summary (lunes 9 AM)
    │     └── low_margin_alert (condicional)
    │
    └──► OBSERVABILIDAD
          ├── Cloud Logging (logs estructurados)
          ├── Cloud Trace (latencia distribuida)
          └── Cloud Monitoring (dashboards + alertas)
```

### Comunicación entre componentes

| Origen → Destino | Protocolo | Autenticación | Latencia |
|---|---|---|---|
| Usuario → API Gateway | HTTPS | API Key | < 50ms |
| API Gateway → Orchestrator | HTTP interno | IAM | < 30ms |
| Orchestrator → Gemini | HTTPS (Vertex AI) | Service Account | 500ms-2s |
| Orchestrator → Tools | HTTP (Cloud Functions) | IAM (invoker) | 100-500ms |
| Tools → Google Sheets | HTTPS (Sheets API) | Service Account | 200-400ms |
| Orchestrator → Workflows | HTTPS (Workflows API) | IAM (invoker) | 100ms (async) |

### Contenerización (Docker)

| Imagen | Base | Multi-stage | Non-root | Tamaño |
|---|---|---|---|---|
| orchestrator | python:3.12-slim | Sí (2 stages) | Sí (appuser) | ~120 MB |
| mock-sheets-api | python:3.12-slim | Sí (2 stages) | Sí (appuser) | ~90 MB |
| logging-service | python:3.12-slim | Sí (2 stages) | Sí (appuser) | ~80 MB |

Secrets manejados externamente: `.env` en desarrollo, GCP Secret Manager en producción. Vulnerability scanning con Trivy integrado en CI/CD.

Detalle completo: Secciones 4 y 6.

---

## 5. Tools

### Inventario

| Tool | Tipo | Función | Modifica estado |
|---|---|---|---|
| `sheets_reader` | Cloud Function | Leer ventas, costos o gastos de Sheets | No |
| `sheets_writer` | Cloud Function | Registrar ventas o gastos nuevos | Sí |
| `calculator` | Cloud Function | Ejecutar cálculos financieros (6 operaciones) | No |
| `report_generator` | Cloud Function | Generar resúmenes estructurados (4 tipos) | No |

### Operaciones del Calculator

| Operación | Descripción |
|---|---|
| `margen_por_sabor` | Margen bruto (%) y absoluto ($) por sabor |
| `margen_por_canal` | Margen bruto por canal (gimnasio vs redes) |
| `proyeccion_ventas` | Proyección a N meses (promedio móvil) |
| `punto_equilibrio` | Unidades mínimas para cubrir costos fijos |
| `resumen_periodo` | Ingresos, costos, gastos y margen de un periodo |
| `comparar_presentaciones` | Rentabilidad 345ml vs 1L |

### Idempotencia

| Tool | Estrategia |
|---|---|
| `sheets_reader` | Natural (función pura, sin estado) |
| `sheets_writer` | Explícita vía `idempotency_key` — detecta duplicados sin insertar |
| `calculator` | Natural (función pura) |
| `report_generator` | Natural (función pura) |

### Códigos de error

20 códigos estandarizados con HTTP status, mensaje descriptivo y acción esperada del agente. Cada tool valida inputs antes de ejecutar y retorna errores estructurados en JSON que el LLM puede interpretar para comunicar al usuario.

Detalle completo: Secciones 5 y 7.

---

## 6. Workflows

| Workflow | Trigger | Pasos | Propósito |
|---|---|---|---|
| `post_write_check` | HTTP (tras cada `sheets_writer`) | 4 | Recalcular acumulados del mes y evaluar si algún sabor tiene margen < 40% |
| `weekly_summary` | Cloud Scheduler (lunes 9 AM) | 5 | Generar resumen semanal automático y almacenarlo en Sheets |
| `low_margin_alert` | Subworkflow (invocado por WF1) | 3 | Generar alerta WARNING cuando un sabor cae bajo el umbral de margen |

### Manejo de errores y reintentos

| Tipo de error | Estrategia |
|---|---|
| Transitorio (429, 502, 503) | Reintento con backoff exponencial (2-30s, max 3 reintentos) |
| Permanente (400, 404) | Fallo inmediato, sin reintento |
| Autenticación (401, 403) | Fallo inmediato, log con severity ERROR |

### Integración con el agente

`post_write_check` se dispara de forma asíncrona (fire-and-forget) tras cada registro exitoso. El usuario recibe la confirmación del registro en 2-3 segundos sin esperar al workflow. Si el workflow detecta margen bajo, genera un log WARNING consultable posteriormente.

Detalle completo: Sección 8.

---

## 7. Estrategias de Optimización

### Costo

| Estrategia | Ahorro | Implementada en MVP |
|---|---|---|
| Small-first (Flash 90% + Pro 10%) | 75% vs solo Pro | Sí |
| Arquitectura serverless (escala a cero) | TCO < $1/mes a volumen actual | Sí |
| Límite de 5 pasos ReAct | Previene costos runaway | Sí |
| Context caching (contenido estático) | 35-94% en input tokens | No (se activa a >500 consultas/mes) |

### Performance

| Estrategia | Mejora | Implementada en MVP |
|---|---|---|
| Gemini Flash como modelo por defecto | 60% menos latencia vs Pro | Sí |
| Límite de pasos (max 5) | Previene latencia runaway | Sí |
| Tool calls combinados (lectura multi-hoja) | -50% latencia en consultas complejas | No (fase posterior) |
| Parallel tool calls | -50% en pasos paralelizables | No (fase posterior) |

### TCO mensual

| Componente | Costo/mes |
|---|---|
| Vertex AI (Gemini Flash + Pro, ~100 consultas) | $0.18 |
| Cloud Functions (~250 invocaciones) | $0.00 (free tier) |
| Cloud Run (orchestrator) | $0.00 (free tier) |
| Google Workflows (~198 pasos) | $0.00 (free tier) |
| Cloud Logging + Trace + Monitoring | $0.00 (free tier) |
| Artifact Registry | $0.03 |
| **Total** | **~$0.21 USD/mes** |

Incluso con crecimiento de 100x (10,000 consultas/mes), el sistema costaría < $20 USD/mes.

Detalle completo: Sección 10.

---

## 8. Pruebas

### Estructura de tests

| Nivel | Archivos | Casos | Qué valida |
|---|---|---|---|
| **Unit** | `test_guardrails.py`, `test_calculator_ops.py` | 19 | Guardrails (13 casos de validación), Calculator (4 operaciones + 1 error handling, 1 edge case) |
| **Integration** | `test_mock_api.py` | 8 | Lectura/escritura del Mock API, idempotencia, errores de hoja inválida |
| **Smoke** | Post-deploy | 2 | Health check + consulta simple end-to-end |

### CI/CD

| Pipeline | Trigger | Pasos |
|---|---|---|
| **CI** (cloudbuild-ci.yaml) | Push / PR | Lint (ruff) → Unit tests → Integration tests → Docker build (×3) → Trivy scan (×3) → Push a Artifact Registry |
| **CD** (cloudbuild-cd.yaml) | Merge a main | Deploy Cloud Functions (×4 en paralelo) → Deploy Cloud Run → Deploy Workflows (×3) → Smoke test |

Si Trivy encuentra vulnerabilidades CRITICAL, el pipeline CI falla y no se despliega.

Detalle completo: Sección 9.

---

## 9. Resultados

### KPIs estimados (basados en diseño y pruebas con Mock API)

| KPI | Meta | Resultado estimado | Estado |
|---|---|---|---|
| Task Success Rate | ≥ 85% | ~90% (18/20 consultas de prueba) | ✅ Cumple |
| Tool-Call Success Rate | ≥ 95% | ~98% (errores solo en edge cases de datos faltantes) | ✅ Cumple |
| Latencia simple | < 8s | ~2-3s (registro, consulta directa) | ✅ Cumple |
| Latencia compleja | < 20s | ~8-12s (resumen, recomendación) | ✅ Cumple |
| Pasos promedio | ≤ 3 | ~2.5 (ponderado por distribución de tareas) | ✅ Cumple |
| Error Handling Rate | ≥ 90% | ~93% (14/15 escenarios manejados correctamente) | ✅ Cumple |

### Cobertura funcional

| Categoría de tarea | Tareas soportadas | Funcionamiento |
|---|---|---|
| Consultas de ventas | 5 (por sabor, canal, presentación, periodo, total) | Operativo |
| Análisis de márgenes | 4 (por sabor, canal, presentación, punto de equilibrio) | Operativo |
| Proyecciones | 1 (promedio móvil a N meses) | Operativo (confianza baja con 3 meses) |
| Recomendaciones | 2 (pricing, producción) | Operativo |
| Registro de datos | 2 (ventas, gastos) | Operativo con idempotencia |
| Resúmenes | 2 (mensual, comparativo) | Operativo |

### Cobertura de tests

| Nivel | Casos | Pasando |
|---|---|---|
| Unit (guardrails) | 13 | 13/13 |
| Unit (calculator) | 6 | 6/6 |
| Integration (mock API) | 8 | 8/8 |
| **Total** | **27** | **27/27** |

---

## 10. Riesgos y Mitigaciones

### Riesgos técnicos

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | Alucinaciones del LLM (cálculos incorrectos) | Media | Alto | El agente NUNCA calcula — delega toda aritmética al tool `calculator`. Guardrails validan rangos. |
| R2 | Cold start en Cloud Functions | Media | Bajo | Cloud Functions 2nd gen (basadas en Cloud Run) reducen cold start. Si se vuelve crítico, configurar `min-instances=1`. |
| R3 | Google Sheets como base de datos | Media | Medio | Aceptable para el volumen actual (~50 registros/mes). Plan de migración a Supabase/Cloud SQL si supera 1,000 registros/mes. |
| R4 | Loops infinitos en ReAct | Baja | Alto | Límite hard de 5 iteraciones. Si se alcanza, responde con lo que tiene y pide reformular. |
| R5 | Cambio de pricing de Gemini/GCP | Baja | Bajo | A este volumen, incluso sin free tier el costo sería < $5/mes. Alertas de billing configuradas. |
| R6 | Latencia alta en horas pico | Baja | Medio | Cloud Run autoescala a 3 instancias. Cloud Functions escalan independientemente hasta 5 instancias cada una. |

### Riesgos operativos

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| R7 | Datos incorrectos en Sheets (errores humanos) | Media | Alto | El agente valida al escribir (guardrails). Para datos existentes, depende de la disciplina de los socios. |
| R8 | Socios no adoptan el agente | Media | Alto | Interfaz en lenguaje natural, sin tecnicismos. Guía de usuario con ejemplos concretos del negocio. |
| R9 | Credenciales comprometidas | Baja | Alto | API Keys en Secret Manager, rotación documentada, permisos least privilege por service account. |
| R10 | Pérdida de datos en Sheets | Baja | Alto | Google Sheets tiene historial de versiones nativo. Recomendación: habilitar backups semanales. |

### Riesgos de modelo

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| R11 | Deprecación del modelo Gemini | Media | Medio | Arquitectura desacoplada: cambiar modelo solo requiere actualizar variable de entorno. Sin dependencia de vendor lock-in en la lógica de negocio. |
| R12 | Datos insuficientes para proyecciones | Alta | Bajo | Con 3 meses de datos, las proyecciones tienen confianza "baja". El agente informa esto al usuario. La confianza mejora automáticamente al acumular más historial. |
| R13 | Sesgo en recomendaciones | Baja | Medio | Las recomendaciones se basan en cálculos del tool `calculator`, no en opinión del LLM. El reporte incluye justificación numérica para que el usuario decida. |

### Matriz de riesgo

```
IMPACTO
  Alto  │ R7  R8  R9    │  R1  R4       │
        │                │               │
 Medio  │ R3  R11        │  R6           │
        │                │               │
  Bajo  │ R2  R12        │  R5  R10  R13 │
        ├────────────────┼───────────────┤
        │     Media      │     Baja      │
                   PROBABILIDAD
```
