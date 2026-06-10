# PROYECTO 3 – Sección 3: Selección y Justificación del Patrón de Diseño LLM (Agentic)

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 3.1 Patrón Principal: ReAct (Reason + Act) + Tool-Calling

### ¿Qué es ReAct?

ReAct (Reasoning and Acting) es un patrón agentic en el que el LLM alterna entre pasos de **razonamiento** (Thought) y **acción** (Action), observando los resultados de cada acción antes de decidir el siguiente paso. A diferencia de un prompt simple donde el modelo responde directamente, ReAct permite que el agente descomponga problemas complejos en pasos secuenciales, invocando herramientas externas cuando necesita datos que no posee.

### ¿Por qué ReAct para BrewFinance Agent?

El agente financiero necesita:

1. **Interpretar** la intención del usuario a partir de lenguaje natural en español
2. **Decidir** qué datos necesita (ventas, costos, o ambos)
3. **Obtener** esos datos desde Google Sheets mediante tools
4. **Calcular** métricas financieras (márgenes, proyecciones, punto de equilibrio)
5. **Generar** una respuesta conversacional con justificación numérica

Esta secuencia no es fija — depende de la pregunta. Una consulta de margen requiere leer ventas Y costos, mientras que un registro de venta solo requiere escribir. ReAct permite que el modelo razone sobre qué herramientas llamar y en qué orden, adaptándose a cada consulta.

---

## 3.2 Diagrama del Flujo ReAct

### Flujo general del ciclo ReAct

```
┌──────────────────────────────────────────────────────────────────────┐
│                        USUARIO                                       │
│  "¿Cuál es mi sabor más rentable este mes?"                         │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  THOUGHT 1                                                           │
│  "El usuario quiere saber qué sabor tiene mayor margen bruto.       │
│   Necesito: (1) datos de ventas del mes actual por sabor,           │
│   (2) costos de producción por sabor. Primero obtengo las ventas."  │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ACTION 1: sheets_reader                                             │
│  {                                                                   │
│    "hoja": "Ventas",                                                 │
│    "filtro": {"mes": "2026-06"},                                     │
│    "campos": ["sabor", "presentacion", "cantidad", "precio_unitario"]│
│  }                                                                   │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  OBSERVATION 1                                                       │
│  [{"sabor":"mango","cantidad":12,"precio":45},                       │
│   {"sabor":"fresa","cantidad":10,"precio":45},                       │
│   {"sabor":"limon","cantidad":8,"precio":40}, ...]                   │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  THOUGHT 2                                                           │
│  "Ya tengo las ventas. Ahora necesito los costos de producción      │
│   por sabor para calcular el margen."                                │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ACTION 2: sheets_reader                                             │
│  {                                                                   │
│    "hoja": "Costos",                                                 │
│    "campos": ["sabor", "costo_ingredientes", "costo_envase",        │
│               "costo_mano_obra"]                                     │
│  }                                                                   │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  OBSERVATION 2                                                       │
│  [{"sabor":"mango","costo_total":17.50},                             │
│   {"sabor":"fresa","costo_total":19.00},                             │
│   {"sabor":"limon","costo_total":15.80}, ...]                        │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  THOUGHT 3                                                           │
│  "Tengo ventas y costos. Calculo margen bruto por sabor:            │
│   margen = precio_unitario - costo_total. Uso la calculadora."      │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ACTION 3: calculator                                                │
│  {                                                                   │
│    "operacion": "margen_por_sabor",                                  │
│    "ventas": [...],                                                  │
│    "costos": [...]                                                   │
│  }                                                                   │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  OBSERVATION 3                                                       │
│  [{"sabor":"mango","margen_pct":61.1,"margen_abs":27.50},            │
│   {"sabor":"limon","margen_pct":60.5,"margen_abs":24.20},            │
│   {"sabor":"fresa","margen_pct":57.8,"margen_abs":26.00}, ...]       │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ANSWER                                                              │
│  "Tu sabor más rentable este mes es mango, con un margen bruto      │
│   del 61.1% ($27.50 por unidad). Le sigue limón con 60.5% y        │
│   fresa con 57.8%. Mango además es tu sabor más vendido (12         │
│   unidades), así que contribuye más a la ganancia total."           │
└──────────────────────────────────────────────────────────────────────┘
```

### Diagrama compacto del ciclo

```
                    ┌──────────┐
                    │ USUARIO  │
                    └────┬─────┘
                         │ pregunta
                         ▼
                  ┌──────────────┐
            ┌────►│   THOUGHT    │
            │     │  (razonar)   │
            │     └──────┬───────┘
            │            │
            │            ▼
            │     ┌──────────────┐       ┌─────────────────┐
            │     │   ACTION     │──────►│  TOOL EXTERNO   │
            │     │  (actuar)    │       │  (Cloud Func.)  │
            │     └──────────────┘       └────────┬────────┘
            │                                     │ resultado
            │     ┌──────────────┐                │
            │     │ OBSERVATION  │◄───────────────┘
            │     │  (observar)  │
            │     └──────┬───────┘
            │            │
            │      ¿Necesito     SÍ
            └──── más datos? ◄───┘
                         │ NO
                         ▼
                  ┌──────────────┐
                  │   ANSWER     │
                  │ (responder)  │
                  └──────┬───────┘
                         │
                         ▼
                    ┌──────────┐
                    │ USUARIO  │
                    └──────────┘
```

---

## 3.3 Explicación del Mecanismo de Decisión

### ¿Cómo decide el agente qué hacer?

El mecanismo de decisión opera en tres niveles:

**Nivel 1 — Clasificación de intención:** El LLM analiza la pregunta del usuario y determina la categoría de tarea (consulta, registro, proyección, recomendación, resumen). Esto define qué tools son candidatos.

**Nivel 2 — Planificación de pasos:** Basándose en la intención y los tools disponibles, el LLM genera un plan implícito. No existe un planificador separado — el propio razonamiento del modelo (Thought) actúa como planificador dentro del ciclo ReAct.

**Nivel 3 — Selección de tool:** El LLM elige el tool específico a invocar emitiendo un `function_call` con el nombre del tool y los parámetros en JSON. Gemini 2.5 Flash realiza esta selección de forma nativa gracias a su soporte de function calling.

### Ejemplo de decisión por tipo de consulta

| Pregunta del usuario | Intención detectada | Tools invocados (en orden) | Pasos ReAct |
|---|---|---|---|
| "¿Cuánto vendí de mango?" | Consulta simple | sheets_reader | 1 |
| "Registra 5 unidades de fresa a $45" | Registro | sheets_writer | 1 |
| "¿Cuál es mi margen por sabor?" | Análisis | sheets_reader → sheets_reader → calculator | 3 |
| "¿Debería subir el precio de limón?" | Recomendación | sheets_reader → sheets_reader → calculator → report_generator | 4 |
| "Dame el resumen del mes" | Resumen | sheets_reader → sheets_reader → calculator → report_generator | 4 |

---

## 3.4 Manejo del Contexto

### Estructura del contexto en cada invocación

```
┌─────────────────────────────────────────────────────────┐
│                  CONTEXT WINDOW                          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ SYSTEM PROMPT                                      │  │
│  │ · Identidad: "Eres BrewFinance Agent..."          │  │
│  │ · Instrucciones: idioma, tono, formato             │  │
│  │ · Reglas: no inventar datos, usar tools siempre    │  │
│  │ · ~400 tokens                                      │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ TOOL DEFINITIONS (function_declarations)           │  │
│  │ · sheets_reader: schema JSON                       │  │
│  │ · sheets_writer: schema JSON                       │  │
│  │ · calculator: schema JSON                          │  │
│  │ · report_generator: schema JSON                    │  │
│  │ · ~400 tokens                                      │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ HISTORIAL DE CONVERSACIÓN (últimos 5 turnos)       │  │
│  │ · user: "¿Cuánto vendí ayer?"                      │  │
│  │ · assistant: "Ayer vendiste 3 de mango..."         │  │
│  │ · user: "¿Y cuál es mi margen en ese sabor?"       │  │
│  │ · ~variable (50-500 tokens)                        │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ MENSAJE ACTUAL DEL USUARIO                         │  │
│  │ · "¿Debería subir el precio?"                      │  │
│  │ · ~50 tokens                                       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  TOTAL ESTIMADO: ~900-1,300 tokens por invocación        │
│  (muy por debajo del límite de 1M tokens de Gemini)      │
└─────────────────────────────────────────────────────────┘
```

### Estrategia de manejo del historial

| Estrategia | Descripción |
|---|---|
| **Ventana deslizante** | Se conservan los últimos 5 turnos de conversación (user + assistant). Los turnos anteriores se descartan. |
| **Exclusión de traces internos** | Los pasos intermedios de ReAct (Thought, Action, Observation) NO se incluyen en el historial — solo la respuesta final (Answer). Esto reduce significativamente el consumo de tokens entre turnos. |
| **Resumen bajo demanda** | Si el usuario pregunta "¿qué hemos hablado?", el agente genera un resumen compacto de la sesión actual. No se persisten conversaciones entre sesiones. |
| **Contexto estático optimizado** | El system prompt y las tool definitions son fijos y se cachean (Gemini soporta context caching), reduciendo el costo de tokens repetidos. |

---

## 3.5 Patrones Complementarios

### Patrón complementario 1: Guardrail Pattern

**Propósito:** Validar que las acciones del agente sean seguras y correctas antes de ejecutarlas. Crítico en un agente financiero que escribe datos en Google Sheets.

```
┌────────────────┐     ┌─────────────────┐     ┌────────────────┐
│  LLM genera    │────►│   GUARDRAIL     │────►│  Ejecución     │
│  function_call │     │   (validación)  │     │  del tool      │
└────────────────┘     └────────┬────────┘     └────────────────┘
                                │
                         ¿Válido?
                        /        \
                      SÍ          NO
                      │            │
               Ejecutar tool    Rechazar y
                               pedir confirmación
```

**Reglas del guardrail para BrewFinance:**

| Regla | Aplica a | Acción si se viola |
|---|---|---|
| Precio unitario debe ser > $0 y < $500 | sheets_writer (ventas) | Rechazar y preguntar al usuario |
| Cantidad debe ser entero positivo ≤ 1,000 | sheets_writer (ventas) | Rechazar y preguntar al usuario |
| Sabor debe existir en el catálogo (5 sabores) | sheets_reader, sheets_writer | Listar sabores válidos |
| Gasto debe tener categoría válida | sheets_writer (gastos) | Sugerir categorías existentes |
| No se puede borrar ni sobrescribir registros existentes | sheets_writer | Bloquear operación |

### Patrón complementario 2: Memory Pattern (Sesión)

**Propósito:** Mantener coherencia dentro de una conversación multi-turno sin persistir datos entre sesiones.

**Implementación:** El historial de conversación (últimos 5 turnos) se pasa como parte del contexto en cada invocación al LLM. Esto permite que el agente resuelva referencias anafóricas como:

| Turno | Mensaje | Sin memory | Con memory |
|---|---|---|---|
| 1 | "¿Cuánto vendí de mango?" | "Vendiste 12 unidades..." | "Vendiste 12 unidades..." |
| 2 | "¿Y cuál es su margen?" | "¿De qué sabor?" (error) | "El margen de mango es 61.1%..." (correcto) |
| 3 | "Compáralo con fresa" | "¿Comparar qué?" (error) | "Mango tiene 61.1% vs fresa 57.8%..." (correcto) |

**Alcance:** Solo memoria de sesión (in-context). No se implementa memoria persistente entre sesiones — cada conversación nueva parte de cero. Esto simplifica la arquitectura y evita problemas de privacidad con datos financieros almacenados.

---

## 3.6 Trade-offs del Patrón Seleccionado

| Ventaja | Desventaja |
|---|---|
| **Flexibilidad:** el agente se adapta a cualquier combinación de tareas sin flujos hardcodeados | **Latencia acumulada:** cada paso ReAct implica una llamada al LLM + una llamada al tool. 3 pasos = 3 round-trips al modelo |
| **Transparencia:** los pasos Thought → Action → Observation generan un trace auditable completo | **Costo proporcional a pasos:** más pasos = más tokens consumidos. Una consulta de 4 pasos cuesta ~4x más que una directa |
| **Simplicidad de implementación:** un solo LLM maneja todo (no hay múltiples agentes ni planificadores separados) | **Dependencia del LLM:** si el modelo elige el tool incorrecto o genera parámetros inválidos, el ciclo falla. Se mitiga con guardrails |
| **Escalabilidad de tools:** agregar un nuevo tool solo requiere declarar un nuevo `function_declaration` — el modelo aprende a usarlo sin reentrenamiento | **Sin paralelismo nativo:** ReAct ejecuta tools secuencialmente. Si el agente necesita ventas Y costos, hace 2 llamadas en serie, no en paralelo |
| **Debugging natural:** el trace de Thought/Action/Observation permite diagnosticar exactamente dónde falló una consulta | **Riesgo de loops:** si el modelo no encuentra la información, puede repetir el mismo tool call indefinidamente. Se mitiga con un límite de 5 iteraciones máximas |

### Mitigaciones implementadas

| Desventaja | Mitigación |
|---|---|
| Latencia acumulada | Usar Gemini 2.5 Flash (optimizado para baja latencia) + Cloud Functions en la misma región GCP |
| Costo proporcional a pasos | Estrategia small-first (Flash para 90% de consultas, Pro solo para complejas) |
| Tool incorrecto seleccionado | Guardrail Pattern valida parámetros antes de ejecutar |
| Sin paralelismo | Aceptable para el volumen actual. Si se requiere, Gemini soporta `parallel_tool_calls` para invocar múltiples tools simultáneamente |
| Riesgo de loops | Límite hard de 5 iteraciones por consulta. Si se alcanza, el agente responde con lo que tiene y explica la limitación |
