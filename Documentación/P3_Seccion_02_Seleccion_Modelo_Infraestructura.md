# PROYECTO 3 – Sección 2: Selección del Modelo + Requerimientos de Infraestructura

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 2.1 Modelos Evaluados

Se evaluaron tres alternativas de LLMs gestionados con soporte nativo de function calling, alineadas con los proveedores sugeridos en la rúbrica del proyecto.

### Opción A: Google Vertex AI — Gemini 2.5 Flash

| Criterio | Detalle |
|---|---|
| Proveedor | Google Cloud (Vertex AI) |
| Modelo | Gemini 2.5 Flash |
| Tipo | Gestionado (API) |
| Contexto máximo | 1,048,576 tokens (1M) |
| Output máximo | 65,536 tokens |
| Function calling | Sí — soporte nativo con `function_declarations` en el parámetro `tools` |
| Thinking (razonamiento) | Sí — configurable por budget de tokens de razonamiento |
| Multimodal | Texto, código, imágenes, audio, video, PDF |
| Costo (input) | $0.30 / 1M tokens |
| Costo (output) | $2.50 / 1M tokens |
| Free tier | Sí — 1,500 RPD (requests per day) en Google AI Studio |

### Opción B: Azure OpenAI — GPT-4o mini

| Criterio | Detalle |
|---|---|
| Proveedor | Microsoft Azure (Azure OpenAI Service) |
| Modelo | GPT-4o mini |
| Tipo | Gestionado (API) |
| Contexto máximo | 128,000 tokens |
| Function calling | Sí — soporte nativo vía `tools` parameter |
| Multimodal | Texto, código, imágenes |
| Costo (input) | $0.15 / 1M tokens |
| Costo (output) | $0.60 / 1M tokens |
| Free tier | No (requiere suscripción Azure) |

### Opción C: AWS Bedrock — Claude 3.5 Haiku

| Criterio | Detalle |
|---|---|
| Proveedor | AWS (Bedrock) |
| Modelo | Claude 3.5 Haiku |
| Tipo | Gestionado (API) |
| Contexto máximo | 200,000 tokens |
| Function calling | Sí — soporte nativo vía `tools` parameter |
| Multimodal | Texto, código, imágenes |
| Costo (input) | $0.80 / 1M tokens |
| Costo (output) | $4.00 / 1M tokens |
| Free tier | No (requiere cuenta AWS con Bedrock habilitado) |

---

## 2.2 Comparativa de Costos por Caso de Uso

Para estimar costos reales, se modeló una interacción típica del agente BrewFinance:

**Supuestos por consulta promedio:**
- System prompt + tool definitions: ~800 tokens (input)
- Pregunta del usuario: ~50 tokens (input)
- Razonamiento ReAct (2-3 pasos): ~500 tokens (output)
- Respuesta final: ~200 tokens (output)
- **Total por consulta: ~850 tokens input / ~700 tokens output**

**Volumen estimado:** ~100 consultas/mes (3 usuarios, ~1-2 consultas/día)

| Modelo | Costo input/mes | Costo output/mes | Costo total/mes |
|---|---|---|---|
| **Gemini 2.5 Flash** | $0.000026 | $0.000175 | **~$0.0002** |
| **GPT-4o mini** | $0.000013 | $0.000042 | **~$0.0001** |
| **Claude 3.5 Haiku** | $0.000068 | $0.000280 | **~$0.0003** |

**Nota:** A este volumen (~100 consultas/mes, ~85K tokens input y ~70K tokens output mensuales), los tres modelos resultan prácticamente gratuitos. La diferencia de costo entre ellos es irrelevante. El criterio de selección se desplaza entonces a otros factores: ecosistema, function calling, latencia e integración con la infraestructura.

---

## 2.3 Justificación de la Selección

### Modelo seleccionado: Gemini 2.5 Flash (Google Vertex AI)

### Modelo de fallback: Gemini 2.5 Pro (Google Vertex AI)

| Factor | Justificación |
|---|---|
| **Capacidad de razonamiento** | Gemini 2.5 Flash incluye capacidad de "thinking" configurable, lo que permite ajustar la profundidad de razonamiento por consulta. Para análisis financiero de una microempresa (márgenes, proyecciones lineales), el modelo es más que suficiente. Para consultas que requieran razonamiento más profundo (recomendaciones de pricing con múltiples variables), se escala al fallback Gemini 2.5 Pro. |
| **Velocidad y costo** | A $0.30/$2.50 por millón de tokens, Gemini 2.5 Flash es uno de los modelos más económicos con capacidad de razonamiento avanzado. Al volumen del proyecto (~100 consultas/mes), el costo de inferencia es esencialmente $0. El free tier de Google AI Studio (1,500 RPD) cubre holgadamente la fase de desarrollo y prototipo. |
| **Soporte nativo de tool-calling** | Gemini 2.5 Flash soporta function calling nativo a través de `function_declarations` en el parámetro `tools`. Esto permite declarar las 4 herramientas del agente (Sheets Reader, Sheets Writer, Calculator, Report Generator) como schemas JSON y que el modelo decida autónomamente cuándo invocar cada una dentro del ciclo ReAct. |
| **Latencia esperada** | Gemini Flash está optimizado para baja latencia en workflows agentic multi-paso. En un ciclo ReAct de 2-3 pasos, se estima una latencia total de 3-6 segundos para consultas simples y 10-15 segundos para análisis complejos — dentro de los KPIs definidos en la Sección 1 (<8s simple, <20s complejo). |
| **Integración con ecosistema** | El negocio ya opera sobre Google Sheets. Usar Vertex AI permite integración nativa con el ecosistema GCP: Google Sheets API, Cloud Functions (serverless), Cloud Logging, y IAM para autenticación. Esto elimina la necesidad de configurar conexiones cross-cloud y reduce la complejidad de infraestructura. |

---

## 2.4 Estrategia de Modelo Dual (Small-First)

El agente implementa una estrategia **small-first** para optimizar costo y latencia:

```
┌─────────────────────────────────────┐
│         CONSULTA DEL USUARIO         │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│         GEMINI 2.5 FLASH            │
│   (modelo principal — rápido)       │
│                                     │
│  ¿La tarea requiere razonamiento    │
│   profundo o el resultado es        │
│   insuficiente?                     │
└──────┬──────────────────┬───────────┘
       │ NO               │ SÍ
       ▼                  ▼
┌──────────────┐  ┌─────────────────┐
│  Respuesta   │  │ GEMINI 2.5 PRO  │
│  directa     │  │ (fallback)      │
│  al usuario  │  │ Razonamiento    │
│              │  │ profundo        │
└──────────────┘  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Respuesta     │
                  │   al usuario    │
                  └─────────────────┘
```

| Modelo | Cuándo se usa | Costo/1M input | Costo/1M output |
|---|---|---|---|
| Gemini 2.5 Flash | ~90% de consultas (márgenes, registros, resúmenes, consultas directas) | $0.30 | $2.50 |
| Gemini 2.5 Pro | ~10% de consultas (proyecciones multi-variable, recomendaciones complejas de pricing) | $1.25 | $10.00 |

---

## 2.5 Requerimientos de Infraestructura

### Servicios de Google Cloud requeridos

| Servicio GCP | Función en la arquitectura | Tier/Plan |
|---|---|---|
| **Vertex AI (Gemini API)** | Inferencia del LLM (function calling + razonamiento) | Pay-as-you-go |
| **Cloud Functions (2nd gen)** | Tools serverless: Sheets Reader, Sheets Writer, Calculator, Report Generator | Free tier (2M invocaciones/mes gratis) |
| **Google Sheets API** | Lectura y escritura de datos de ventas, costos y gastos | Sin costo (cuota estándar: 300 requests/min) |
| **Cloud Logging** | Logs estructurados del agente, tools y errores | Free tier (50 GB/mes gratis) |
| **Cloud Trace** | Trazabilidad de latencia por tool call | Free tier (primeros 2.5M spans gratis) |
| **Secret Manager** | Almacenamiento de API keys y credenciales de Sheets | Free tier (6 versiones de secreto activas gratis) |
| **Artifact Registry** | Almacenamiento de imágenes Docker del orquestador | $0.10/GB (primeros 0.5 GB gratis) |

### Estimación de costo mensual total

| Componente | Costo estimado/mes |
|---|---|
| Vertex AI (Gemini 2.5 Flash, ~100 consultas) | ~$0.00 (free tier cubre) |
| Cloud Functions (~100 invocaciones × 4 tools) | ~$0.00 (dentro de free tier de 2M) |
| Google Sheets API | $0.00 |
| Cloud Logging | ~$0.00 (dentro de free tier) |
| Cloud Trace | ~$0.00 (dentro de free tier) |
| Secret Manager | ~$0.00 (dentro de free tier) |
| Artifact Registry | ~$0.01 |
| **Total estimado** | **< $1.00 USD/mes** |

**Conclusión de costos:** Para una microempresa con ~100 consultas mensuales al agente, la infraestructura completa en GCP cae dentro de los free tiers de prácticamente todos los servicios. El costo operativo real es cercano a cero, lo que valida la elección de una arquitectura serverless pay-as-you-go como la opción más eficiente.

---

## 2.6 Riesgos y Restricciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **Cold start en Cloud Functions** | Media | Latencia de 1-3s adicionales en la primera invocación tras inactividad | Usar Cloud Functions 2nd gen (basadas en Cloud Run) con `min-instances=1` si la latencia se vuelve crítica |
| **Alucinaciones del LLM** | Media | El agente podría generar cálculos o recomendaciones incorrectas | Validar resultados numéricos con la herramienta Calculator (no depender del LLM para aritmética), incluir guardrails de rango |
| **Cambios en pricing de Gemini** | Baja | Aumento de costos si Google modifica free tiers | A este volumen, incluso sin free tier el costo mensual sería < $1. Monitorear con alertas de billing en GCP |
| **Dependencia de Google Sheets como BD** | Media | Limitaciones de concurrencia, sin transaccionalidad ACID, límite de 10M celdas | Aceptable para el volumen actual. Si el negocio escala a >1,000 registros/mes, migrar a Supabase o Cloud SQL |
| **Límite de contexto en conversaciones largas** | Baja | En conversaciones muy extendidas, el contexto podría exceder el budget óptimo de tokens | Implementar resumen de conversación y limitar historial a últimos 5 turnos |
| **Disponibilidad de Vertex AI en LATAM** | Baja | Posibles restricciones regionales o latencia por ubicación del endpoint | Usar endpoint global de Vertex AI; la latencia adicional (~50-100ms) es aceptable para este caso de uso |
