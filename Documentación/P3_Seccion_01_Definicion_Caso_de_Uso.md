# PROYECTO 3 – Sección 1: Definición Avanzada del Caso de Uso del Agente

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 1.1 Escenario Real

### Contexto del negocio

Microempresa de bebidas embotelladas artesanales con 3 meses de operación en México. El negocio produce 5 sabores diferenciados, cada uno con costos de producción distintos, y comercializa en dos presentaciones: 345ml y 1L.

| Dato operativo | Valor actual |
|---|---|
| Volumen mensual aproximado | ~40 unidades (345ml) + ~3 unidades (1L) |
| Sabores en catálogo | 5 (cada uno con costo de producción individual) |
| Canales de venta | Gimnasio de escalada (cliente principal) + venta directa por redes sociales |
| Historial de ventas | 3 meses registrados en Google Sheets |
| Historial de gastos | 1 mes registrado (último mes) |
| Equipo | 2-3 socios |

### Problema identificado

El emprendimiento toma decisiones de pricing, producción y distribución entre canales de forma intuitiva. Los datos de ventas y costos existen en Google Sheets pero no se analizan de forma sistemática: no hay visibilidad sobre márgenes reales por sabor ni por canal, no se proyecta demanda, y no se evalúa qué combinación de productos maximiza la rentabilidad. A medida que el negocio crece (nuevos puntos de venta, más sabores), la toma de decisiones sin datos se vuelve un riesgo operativo.

### Solución propuesta

**BrewFinance Agent** — Un agente conversacional inteligente que se conecta a los Google Sheets del negocio, analiza datos financieros, genera recomendaciones accionables y registra información nueva, todo a través de lenguaje natural en español.

**Categoría del agente:** Agente financiero para microempresa (simulado con datos reales).

---

## 1.2 Usuarios Objetivo

| Usuario | Rol en el negocio | Interacción con el agente | Preguntas típicas |
|---|---|---|---|
| **Fundador (Francisco)** | Decisor estratégico y financiero | Consultas de márgenes, pricing, proyecciones, registro de gastos | "¿Cuál es mi sabor más rentable?", "¿Debería subir el precio del sabor X?" |
| **Socio de producción** | Operaciones y formulación | Consultas de costos, volúmenes óptimos de producción | "¿Cuánto me cuesta producir un lote de mango?", "¿Qué sabor tiene peor margen?" |
| **Socio de ventas** | Comercialización y distribución | Tendencias de venta por canal, desempeño por cliente | "¿Qué porcentaje viene del gimnasio vs redes?", "¿Qué sabor se vende más en 345ml?" |

**Perfil técnico de los usuarios:** No técnicos. El agente debe responder en español conversacional, sin requerir conocimiento de datos, APIs o dashboards.

**Interfaz de interacción:** Chat en texto (lenguaje natural), con experiencia tipo WhatsApp/Telegram.

---

## 1.3 Flujo Completo de Tareas del Agente

### Diagrama de flujo general

```
┌─────────────────────────────────────────────────────────────┐
│                     USUARIO                                  │
│          (pregunta en lenguaje natural, español)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   API GATEWAY                                │
│         (Cloud Function / HTTP Trigger)                      │
│     Autenticación · Rate Limiting · Input Validation         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              AGENTE ORQUESTADOR (ReAct Loop)                 │
│                                                              │
│   1. THOUGHT  → Analiza la intención del usuario             │
│   2. ACTION   → Selecciona tool(s) necesarios                │
│   3. OBSERVE  → Recibe resultado del tool                    │
│   4. REPEAT   → Si necesita más datos, vuelve a paso 1      │
│   5. ANSWER   → Genera respuesta final al usuario            │
│                                                              │
│   Modelo principal: Gemini 2.0 Flash                         │
│   Fallback: Gemini 1.5 Pro (razonamiento complejo)           │
└───┬───────────┬───────────┬───────────┬─────────────────────┘
    │           │           │           │
    ▼           ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌─────────┐ ┌──────────┐
│ TOOL 1 │ │ TOOL 2 │ │ TOOL 3  │ │ TOOL 4   │
│ Sheets │ │ Sheets │ │ Calc /  │ │ Report   │
│ Reader │ │ Writer │ │Analytics│ │ Gen      │
└───┬────┘ └───┬────┘ └─────────┘ └──────────┘
    │          │
    ▼          ▼
┌─────────────────────┐
│   GOOGLE SHEETS     │
│   (Data Store)      │
│  · Hoja: Ventas     │
│  · Hoja: Costos     │
│  · Hoja: Gastos     │
└─────────────────────┘
```

### Tareas soportadas por el agente

| # | Tarea | Tools involucrados | Pasos esperados | Complejidad |
|---|---|---|---|---|
| T1 | Consultar margen por sabor | Sheets Reader → Calculator | 2 | Baja |
| T2 | Consultar ventas por canal (gimnasio vs redes) | Sheets Reader → Calculator | 2 | Baja |
| T3 | Consultar ventas por presentación (345ml vs 1L) | Sheets Reader → Calculator | 2 | Baja |
| T4 | Proyectar ventas a N meses | Sheets Reader → Calculator | 3 | Media |
| T5 | Recomendar ajuste de precio | Sheets Reader → Calculator → Report Gen | 3-4 | Media |
| T6 | Generar resumen financiero del mes | Sheets Reader → Calculator → Report Gen | 3-4 | Media |
| T7 | Registrar venta nueva | Sheets Writer | 1 | Baja |
| T8 | Registrar gasto nuevo | Sheets Writer | 1 | Baja |
| T9 | Comparar rentabilidad entre sabores | Sheets Reader → Calculator → Report Gen | 3 | Media |
| T10 | Calcular punto de equilibrio por sabor | Sheets Reader → Calculator | 2-3 | Media |

---

## 1.4 Límites del Sistema

### Dentro del alcance (In-Scope)

- Análisis financiero basado exclusivamente en datos del Google Sheets del negocio
- Cálculo de márgenes brutos por sabor, por presentación y por canal
- Proyecciones de demanda basadas en tendencia histórica (promedio móvil, regresión lineal simple sobre 3 meses de datos)
- Recomendaciones de pricing con justificación numérica
- Cálculo de punto de equilibrio por producto
- Registro de ventas y gastos nuevos directamente en Google Sheets
- Generación de resúmenes financieros periódicos en texto
- Respuestas en español conversacional

### Fuera del alcance (Out-of-Scope)

- Gestión de inventario físico, stock o cadena de suministro
- Análisis de mercado externo, competencia o benchmarking
- Facturación electrónica, contabilidad fiscal o cumplimiento regulatorio (SAT)
- Modelos predictivos con ML avanzado (el agente usa estadística descriptiva y proyecciones lineales)
- Transacciones bancarias, cobros o pagos
- Procesamiento de imágenes o documentos (solo texto/JSON)
- Soporte multiidioma (solo español)

### Supuestos del sistema

- Los datos en Google Sheets son correctos y están actualizados por los socios
- La estructura de las hojas (columnas, nombres) se mantiene estable
- El volumen de consultas es bajo (< 100/mes en fase inicial)
- Los usuarios tienen conectividad a internet para usar el chat

---

## 1.5 Inputs / Outputs

### Inputs

| Tipo de input | Formato | Ejemplo concreto |
|---|---|---|
| Pregunta de consulta | Texto libre (español) | "¿Cuánto gané este mes con el sabor de mango?" |
| Pregunta de proyección | Texto libre (español) | "Si sigo vendiendo igual, ¿cuánto venderé en diciembre?" |
| Solicitud de recomendación | Texto libre (español) | "¿Debería dejar de producir el sabor menos rentable?" |
| Registro de venta | Texto libre → JSON | "Vendí 8 de fresa 345ml a $45 en el gimnasio" → `{"tipo":"venta", "sabor":"fresa", "presentacion":"345ml", "cantidad":8, "precio_unitario":45, "canal":"gimnasio"}` |
| Registro de gasto | Texto libre → JSON | "Gasté $500 en envases esta semana" → `{"tipo":"gasto", "categoria":"envases", "monto":500, "fecha":"2026-05-26"}` |

### Outputs

| Tipo de output | Formato | Ejemplo concreto |
|---|---|---|
| Respuesta analítica | Texto conversacional (español) | "Este mes el sabor mango te generó $1,800 en ingresos con un costo de $680, lo que deja un margen bruto de $1,120 (62%). Es tu sabor más rentable." |
| Datos estructurados | JSON (interno, para logging) | `{"query_type":"margin_analysis", "sabor":"mango", "ingresos":1800, "costo":680, "margen_pct":62.2}` |
| Recomendación | Texto con justificación numérica | "Recomiendo subir el precio de limón 345ml de $40 a $45. Tu margen actual es 38%, con el ajuste subiría a 47% sin afectar significativamente el volumen (es tu 4to sabor en ventas)." |
| Confirmación de registro | Texto + escritura en Sheets | "Listo, registré 8 unidades de fresa 345ml a $45 en el canal gimnasio con fecha 26/05/2026." |
| Resumen periódico | Texto estructurado | "Resumen mayo 2026: Ingresos totales $4,200 | Costos totales $1,900 | Margen bruto $2,300 (55%) | Sabor top: mango (62%) | Canal top: gimnasio (78% del volumen)" |

---

## 1.6 KPIs del Agente

| KPI | Definición | Fórmula | Meta | Método de medición |
|---|---|---|---|---|
| **Task Success Rate** | Porcentaje de tareas que el agente completa correctamente con respuesta útil y precisa | (Tareas exitosas / Tareas totales) × 100 | ≥ 85% | Evaluación manual sobre un set de 20 consultas de prueba representativas (4 por categoría: margen, proyección, registro, recomendación, resumen) |
| **Tool-Call Success Rate** | Porcentaje de invocaciones a tools que retornan resultado exitoso (HTTP 200 + datos válidos) | (Tool calls exitosos / Tool calls totales) × 100 | ≥ 95% | Logs estructurados del agente: cada tool call registra status code y payload de respuesta |
| **Latencia de resolución** | Tiempo transcurrido desde que el usuario envía la pregunta hasta que recibe la respuesta completa | timestamp_response - timestamp_request | < 8s (consultas simples), < 20s (análisis complejos) | Timestamps en el pipeline: inicio del request (API Gateway) → fin del response (agente) |
| **Pasos promedio por tarea** | Cantidad de ciclos ReAct (Thought → Action → Observation) necesarios para completar una tarea | Σ pasos / Σ tareas | ≤ 3 pasos promedio | Conteo de tool calls en el trace del agente por cada conversación |
| **Error Handling Rate** | Porcentaje de errores (Sheets no disponible, datos faltantes, pregunta ambigua) que el agente detecta y comunica al usuario de forma clara | (Errores manejados correctamente / Errores totales) × 100 | ≥ 90% | Escenarios de fallo inducidos: 5 tests con Sheets offline, 5 con datos faltantes, 5 con preguntas ambiguas |

### Escenarios de prueba para Error Handling

| # | Escenario de fallo | Comportamiento esperado del agente |
|---|---|---|
| E1 | Google Sheets no disponible (API timeout) | "No puedo acceder a tus datos en este momento. Intenta de nuevo en unos minutos." |
| E2 | Hoja de costos vacía para un sabor | "No tengo registrado el costo de producción de [sabor]. ¿Puedes registrarlo primero?" |
| E3 | Pregunta ambigua: "¿Cómo voy?" | "¿Te refieres a las ventas de este mes, al margen general o a algún sabor en particular?" |
| E4 | Sabor no reconocido: "¿Cuánto vendí de uva?" | "No tengo un sabor llamado 'uva' en tu catálogo. Tus sabores son: [lista]. ¿Te refieres a alguno de estos?" |
| E5 | Registro con datos incompletos: "Vendí fresa" | "Para registrar la venta necesito: cantidad, presentación (345ml o 1L), precio y canal. ¿Me los das?" |


