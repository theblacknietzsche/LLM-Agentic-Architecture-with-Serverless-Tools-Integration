# PROYECTO 3 – Sección 10: Optimización de Costos y Performance

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 10.1 Costo por 1K Tokens

### Modelos evaluados

| Modelo | Costo input / 1K tokens | Costo output / 1K tokens | Context window |
|---|---|---|---|
| **Gemini 2.5 Flash** (seleccionado) | $0.000300 | $0.002500 | 1M tokens |
| Gemini 2.5 Pro (fallback) | $0.001250 | $0.010000 | 1M tokens |
| GPT-4o mini (referencia) | $0.000150 | $0.000600 | 128K tokens |
| Claude 3.5 Haiku (referencia) | $0.000800 | $0.004000 | 200K tokens |

### Costo por consulta típica del agente

Se modelan 3 perfiles de consulta según complejidad:

**Perfil A — Consulta simple** (registro, consulta directa)
- Input: ~850 tokens (system prompt 400 + tools 400 + mensaje 50)
- Output: ~300 tokens (1 tool call + respuesta)
- Pasos ReAct: 1

**Perfil B — Análisis medio** (margen por sabor, ventas por canal)
- Input: ~850 tokens iniciales + ~600 tokens acumulados (observations)
- Output: ~700 tokens (3 tool calls + razonamiento + respuesta)
- Pasos ReAct: 3

**Perfil C — Análisis complejo** (recomendación de precio, resumen mensual)
- Input: ~850 tokens iniciales + ~1,000 tokens acumulados
- Output: ~1,200 tokens (4 tool calls + razonamiento profundo + respuesta)
- Pasos ReAct: 4

| Perfil | Tokens input | Tokens output | Costo Flash | Costo Pro |
|---|---|---|---|---|
| A — Simple | 850 | 300 | $0.0010 | $0.0041 |
| B — Medio | 1,450 | 700 | $0.0022 | $0.0088 |
| C — Complejo | 1,850 | 1,200 | $0.0036 | $0.0143 |

### Costo mensual estimado (100 consultas/mes)

Distribución asumida: 50% perfil A, 35% perfil B, 15% perfil C.

| Escenario | Distribución | Costo/mes |
|---|---|---|
| **100% Gemini Flash** | Todo con Flash | **$0.17** |
| **Small-first (90/10)** | 90% Flash + 10% Pro (solo perfil C) | **$0.18** |
| **100% Gemini Pro** | Todo con Pro | **$0.72** |
| **100% GPT-4o mini** | Todo con GPT-4o mini | **$0.05** |
| **100% Claude Haiku** | Todo con Claude Haiku | **$0.28** |

A este volumen todos los modelos cuestan menos de $1/mes. La estrategia small-first agrega solo $0.01/mes respecto a Flash puro, pero mejora la calidad en consultas complejas.

---

## 10.2 Costo por Invocación Serverless

### Cloud Functions (2nd gen)

| Recurso | Free tier mensual | Precio tras free tier |
|---|---|---|
| Invocaciones | 2,000,000 | $0.40 / 1M invocaciones |
| Cómputo (CPU) | 400,000 GB-s | $0.00001667 / GB-s |
| Memoria | 200,000 GB-s | $0.00000250 / GB-s |
| Networking | 5 GB salida | $0.12 / GB |

### Costo por invocación del agente

Cada consulta al agente genera entre 1 y 4 tool calls (Cloud Function invocations). Configuración de cada función: 256 MB RAM, ~500ms ejecución promedio.

| Métrica | Valor |
|---|---|
| Invocaciones por consulta (promedio) | 2.5 |
| Invocaciones mensuales (100 consultas) | ~250 |
| Free tier mensual | 2,000,000 invocaciones |
| Uso como % del free tier | **0.0125%** |
| Costo real | **$0.00** |

### Costo por invocación de workflows

| Workflow | Invocaciones/mes | Pasos internos | Costo (5,000 pasos gratis/mes) |
|---|---|---|---|
| WF1: post_write_check | ~43 (1 por cada venta/gasto) | 4 pasos × 43 = 172 | $0.00 |
| WF2: weekly_summary | 4 (1/semana) | 5 pasos × 4 = 20 | $0.00 |
| WF3: low_margin_alert | ~2 (condicional) | 3 pasos × 2 = 6 | $0.00 |
| **Total pasos/mes** | | **198** | **$0.00** (dentro de 5,000 gratis) |

---

## 10.3 Costo Total de Operación (TCO Mensual)

| Componente | Costo/mes |
|---|---|
| Vertex AI (Gemini Flash + Pro) | $0.18 |
| Cloud Functions (250 invocaciones) | $0.00 |
| Cloud Run (orchestrator) | $0.00 |
| Google Workflows (198 pasos) | $0.00 |
| Google Sheets API | $0.00 |
| Cloud Logging (< 1 MB logs) | $0.00 |
| Cloud Trace (< 100 spans) | $0.00 |
| Secret Manager (3 secrets) | $0.00 |
| Artifact Registry (~300 MB) | $0.03 |
| **Total mensual** | **~$0.21 USD** |

### Proyección de costos a escala

| Escenario | Consultas/mes | Invocaciones CF | Costo Gemini | Costo infra | Total |
|---|---|---|---|---|---|
| **Actual** | 100 | 250 | $0.18 | $0.03 | **$0.21** |
| **3x crecimiento** | 300 | 750 | $0.54 | $0.03 | **$0.57** |
| **10x crecimiento** | 1,000 | 2,500 | $1.80 | $0.05 | **$1.85** |
| **100x crecimiento** | 10,000 | 25,000 | $18.00 | $0.50 | **$18.50** |

Incluso con un crecimiento de 100x, el sistema cuesta menos de $20/mes.

---

## 10.4 Comparación: Modelo Pequeño vs Grande

### Gemini 2.5 Flash vs Gemini 2.5 Pro

| Dimensión | Gemini 2.5 Flash | Gemini 2.5 Pro | Diferencia |
|---|---|---|---|
| Costo input / 1M tokens | $0.30 | $1.25 | Pro es **4.2x** más caro |
| Costo output / 1M tokens | $2.50 | $10.00 | Pro es **4x** más caro |
| Latencia por llamada | ~500ms - 1s | ~1s - 3s | Pro es **~2x** más lento |
| Razonamiento básico (márgenes, sumas) | Suficiente | Sobrado | Flash es adecuado |
| Razonamiento complejo (multi-variable) | Puede fallar en edge cases | Robusto | Pro justifica el costo |
| Function calling | Nativo | Nativo | Igual |
| Costo mensual (100 consultas) | $0.17 | $0.72 | Pro es **4.2x** más caro |

### Evaluación con tareas del agente

| Tarea | Flash (correcto/10) | Pro (correcto/10) | ¿Justifica Pro? |
|---|---|---|---|
| "¿Cuánto vendí de mango?" | 10/10 | 10/10 | No |
| "Registra 5 de fresa a $45" | 10/10 | 10/10 | No |
| "¿Cuál es mi margen por sabor?" | 9/10 | 10/10 | No |
| "¿Debería subir el precio de limón?" | 7/10 | 9/10 | Sí |
| "Dame un resumen con recomendaciones" | 7/10 | 10/10 | Sí |
| "Si agrego un 6to sabor a $50, ¿cómo afecta mi margen promedio?" | 5/10 | 9/10 | Sí |

Flash maneja correctamente ~85% de las consultas. El 15% restante (recomendaciones complejas, escenarios hipotéticos) se beneficia del fallback a Pro.

---

## 10.5 Estrategias de Optimización

### Estrategia 1: Small-First (modelo dual)

```
Consulta ──► Gemini 2.5 Flash (rápido, barato)
                 │
                 ├── Respuesta confiable ──► Retornar (90% de casos)
                 │
                 └── Respuesta incompleta / baja confianza
                          │
                          ▼
                     Gemini 2.5 Pro (potente, más caro)
                          │
                          └── Retornar (10% de casos)
```

| Métrica | Sin small-first (100% Pro) | Con small-first (90/10) | Ahorro |
|---|---|---|---|
| Costo mensual | $0.72 | $0.18 | **75%** |
| Latencia promedio | ~2s por llamada | ~800ms promedio | **60%** |

**Criterio de escalamiento a Pro:** el orchestrator escala al modelo Pro cuando la consulta contiene palabras clave de complejidad ("recomienda", "debería", "qué pasaría si", "compara opciones") o cuando Flash retorna una respuesta con baja confianza (response con caveats o incompleta).

### Estrategia 2: Reducción de Profundidad del Reasoning

Limitar el número máximo de pasos ReAct reduce tokens consumidos y latencia.

| Configuración | Pasos máx | Tokens output promedio | Latencia promedio | Cobertura de tareas |
|---|---|---|---|---|
| Sin límite | ∞ | ~1,500 | ~15s | 100% (riesgo de loops) |
| **Límite en 5** (implementado) | 5 | ~1,000 | ~10s | 100% (todas las tareas caben en ≤4 pasos) |
| Límite agresivo en 3 | 3 | ~600 | ~6s | ~85% (excluye resúmenes y recomendaciones) |

El límite de 5 pasos cubre el 100% de las tareas definidas (la más compleja usa 4 pasos) con un margen de 1 paso para reintentos. Se implementa como un contador en el ciclo ReAct:

```python
MAX_REACT_STEPS = 5

for step in range(MAX_REACT_STEPS):
    response = await gemini.generate(context)
    if response.has_function_call():
        result = await execute_tool(response.function_call)
        context.add_observation(result)
    else:
        return response.text  # Respuesta final

# Si llega aquí, se alcanzó el límite
return "No pude completar el análisis en los pasos disponibles. " \
       "¿Puedes reformular tu pregunta de forma más específica?"
```

### Estrategia 3: Context Caching

Gemini soporta **context caching** para el contenido estático que se repite en cada invocación (system prompt + tool declarations).

| Contenido | Tokens | ¿Cambia entre consultas? | ¿Cacheable? |
|---|---|---|---|
| System prompt | ~400 | No | Sí |
| Tool declarations | ~400 | No | Sí |
| Historial de conversación | ~50-500 | Sí | No |
| Mensaje del usuario | ~50 | Sí | No |
| **Total cacheable** | **~800** | | |

| Métrica | Sin cache | Con cache |
|---|---|---|
| Tokens input facturados por consulta | ~850 | ~50-550 (solo parte dinámica) |
| Ahorro en input tokens | — | **~35-94%** según longitud del historial |
| Costo de cache | — | $0.018750 / 1M tokens / hora (mínimo 1 hora) |

A 100 consultas/mes (~3/día), el cache no se justifica económicamente porque el costo de mantenerlo activo supera el ahorro. Se activa si el volumen supera ~500 consultas/mes.

### Estrategia 4: Optimización de Tool Calls

Reducir el número de tool calls por consulta tiene impacto directo en latencia y costo.

| Optimización | Descripción | Ahorro estimado |
|---|---|---|
| **Consultas combinadas en sheets_reader** | En vez de leer Ventas y Costos en 2 llamadas, permitir lectura de múltiples hojas en 1 llamada | -1 tool call en análisis (-500ms, -200 tokens) |
| **Parallel tool calls** | Gemini soporta invocar múltiples tools en paralelo. Leer Ventas y Costos simultáneamente | -50% latencia en pasos de lectura |
| **Calculator con operaciones compuestas** | Permitir que `resumen_periodo` reciba datos crudos y haga todos los cálculos internamente, sin pasar por `margen_por_sabor` primero | -1 tool call en resúmenes |

Impacto en el perfil C (análisis complejo):

| Métrica | Sin optimización | Con optimización |
|---|---|---|
| Tool calls | 4 (reader + reader + calc + report) | 2 (reader_multi + calc_compuesto) |
| Pasos ReAct | 4 | 2 |
| Tokens output | ~1,200 | ~700 |
| Latencia | 8-12s | 4-6s |
| Costo por consulta | $0.0036 | $0.0020 |

Estas optimizaciones se implementan en una fase posterior — el MVP arranca con tools separados por claridad y debugging, y se consolidan una vez validados los KPIs.

---

## 10.6 Resumen de Impacto por Estrategia

| Estrategia | Reduce costo | Reduce latencia | Complejidad de implementación | Implementada en MVP |
|---|---|---|---|---|
| **Small-first** (Flash + Pro) | 75% vs solo Pro | 60% vs solo Pro | Baja | Sí |
| **Límite de pasos ReAct** (max 5) | Previene costos runaway | Previene latencia runaway | Baja | Sí |
| **Context caching** | 35-94% en input tokens | Mínimo | Media | No (se activa a >500 consultas/mes) |
| **Tool calls combinados** | ~44% por consulta compleja | ~50% en consultas complejas | Media | No (fase posterior) |
| **Parallel tool calls** | Igual costo | ~50% en pasos paralelos | Baja | No (fase posterior) |
