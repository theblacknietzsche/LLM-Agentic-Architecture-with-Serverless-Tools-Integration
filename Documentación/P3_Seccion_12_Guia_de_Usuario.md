# PROYECTO 3 – Sección 12: Guía de Usuario

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco  
**Documento:** Guía de Usuario — BrewFinance Agent v1.0.0

---

## 1. ¿Qué es BrewFinance Agent?

BrewFinance Agent es un asistente financiero conversacional diseñado para la microempresa de bebidas embotelladas artesanales. Permite consultar ventas, analizar márgenes, registrar transacciones, obtener proyecciones y recibir recomendaciones de pricing — todo a través de mensajes de texto en español, como si hablaras con un socio que tiene todos los números a la mano.

### ¿Quién puede usarlo?

| Usuario | Qué puede hacer |
|---|---|
| Fundador / Socio estratégico | Consultar márgenes, pedir recomendaciones de precio, obtener resúmenes financieros |
| Socio de producción | Consultar costos por sabor, identificar el sabor más y menos rentable |
| Socio de ventas | Ver tendencias por canal, registrar ventas, comparar desempeño gimnasio vs redes |

---

## 2. Cómo Acceder al Agente

### Paso 1: Obtener tu API Key

El administrador del sistema te proporcionará una API Key personal. Es una cadena de texto como `bf-user-francisco-2026`. Guárdala de forma segura — es tu llave de acceso.

### Paso 2: Enviar un mensaje

Envía un mensaje HTTP POST al endpoint del agente. Puedes hacerlo desde cualquier herramienta que envíe requests HTTP:

**Usando curl (terminal):**

```bash
curl -X POST https://brewfinance-orchestrator-XXXXX.run.app/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{"message": "¿Cuál es mi sabor más rentable?"}'
```

**Usando un cliente HTTP (Postman, Insomnia, Thunder Client):**

```
Método: POST
URL: https://brewfinance-orchestrator-XXXXX.run.app/chat
Headers:
  Content-Type: application/json
  X-API-Key: TU_API_KEY
Body (JSON):
  {"message": "¿Cuál es mi sabor más rentable?"}
```

### Paso 3: Leer la respuesta

El agente responde en JSON con el campo `message` que contiene la respuesta en español:

```json
{
  "request_id": "req-a1b2c3d4e5f6",
  "message": "Tu sabor más rentable este mes es mango con un margen bruto del 61.1% (27.50 MXN por unidad). Le sigue limón con 60.5% y menta con 62.2%.",
  "model_used": "gemini-2.5-flash",
  "steps": 3,
  "latency_ms": 4230,
  "tool_calls": ["sheets_reader", "sheets_reader", "calculator"]
}
```

El campo `message` es tu respuesta. Los demás campos son informativos.

---

## 3. Qué Puedes Preguntarle al Agente

### 3.1 Consultas de Ventas

| Pregunta de ejemplo | Qué obtienes |
|---|---|
| "¿Cuánto vendí este mes?" | Total de unidades y ingresos del mes actual |
| "¿Cuánto vendí de mango en junio?" | Ventas filtradas por sabor y mes |
| "¿Qué sabor se vende más?" | Ranking de sabores por volumen |
| "¿Cuánto vendí en el gimnasio vs redes?" | Comparación por canal de venta |
| "¿Cuántas botellas de 1L vendí?" | Ventas filtradas por presentación |

### 3.2 Consultas de Márgenes y Rentabilidad

| Pregunta de ejemplo | Qué obtienes |
|---|---|
| "¿Cuál es mi sabor más rentable?" | Ranking de sabores por margen bruto (%) |
| "¿Cuál es el margen de fresa?" | Margen bruto específico de un sabor |
| "¿Cuánto me cuesta producir cada sabor?" | Desglose de costos por sabor |
| "¿Cuál es mi punto de equilibrio?" | Unidades mínimas para cubrir costos fijos |
| "Compara la rentabilidad de 345ml vs 1L" | Margen por presentación |

### 3.3 Proyecciones

| Pregunta de ejemplo | Qué obtienes |
|---|---|
| "Si sigo vendiendo igual, ¿cuánto venderé en 3 meses?" | Proyección basada en promedio móvil |
| "¿Cómo va la tendencia de ventas?" | Análisis de tendencia (creciente/decreciente/estable) |

### 3.4 Recomendaciones

| Pregunta de ejemplo | Qué obtienes |
|---|---|
| "¿Debería subir el precio de limón?" | Análisis con precio sugerido y justificación numérica |
| "¿Qué sabor debería dejar de producir?" | Recomendación basada en margen y volumen |
| "Dame recomendaciones para mejorar mi margen" | Análisis general con acciones sugeridas |

### 3.5 Registro de Datos

| Pregunta de ejemplo | Qué hace el agente |
|---|---|
| "Registra que vendí 10 de mango a 45 pesos en el gimnasio" | Inserta una fila en la hoja Ventas |
| "Registra un gasto de 500 pesos en envases" | Inserta una fila en la hoja Gastos |
| "Vendí 3 de fresa 1L a 90 pesos por redes" | Inserta una venta con presentación 1L |

### 3.6 Resúmenes

| Pregunta de ejemplo | Qué obtienes |
|---|---|
| "Dame el resumen del mes" | Ingresos, costos, gastos, margen bruto y neto |
| "¿Cómo va junio comparado con mayo?" | Comparativa entre meses |
| "Resume las ventas de esta semana" | Resumen del periodo solicitado |

---

## 4. Cómo Registrar una Venta

### Paso a paso

**1. Escribe la venta en lenguaje natural:**

```
"Vendí 8 de fresa 345ml a 45 pesos en el gimnasio"
```

**2. El agente parsea tu mensaje y te pide confirmación si falta algo:**

Si dijiste "vendí fresa", el agente responderá:
```
"Para registrar la venta necesito: cantidad, presentación (345ml o 1L), precio y canal. ¿Me los das?"
```

**3. El agente registra y confirma:**

```
"Listo, registré 8 unidades de fresa 345ml a 45 MXN en el canal gimnasio con fecha 15/06/2026."
```

### Datos necesarios para registrar una venta

| Dato | Valores válidos | Ejemplo |
|---|---|---|
| Sabor | mango, fresa, limon, jengibre, menta | "mango" |
| Cantidad | Número entero positivo (1 a 1,000) | "10" |
| Presentación | 345ml o 1L | "345ml" |
| Precio unitario | Mayor a 0, hasta 500 MXN | "45" |
| Canal | gimnasio o redes | "gimnasio" |
| Fecha | Se asume hoy si no la mencionas | "15 de junio" |

### Datos necesarios para registrar un gasto

| Dato | Valores válidos | Ejemplo |
|---|---|---|
| Categoría | ingredientes, envases, transporte, marketing, operativo, otro | "envases" |
| Monto | Mayor a 0, hasta 100,000 MXN | "500" |
| Descripción | Texto libre (opcional) | "Botellas 345ml x100" |
| Fecha | Se asume hoy si no la mencionas | "1 de junio" |

---

## 5. Cómo Interpretar las Respuestas

### Márgenes

- **Margen bruto (%):** Qué porcentaje del precio de venta queda después de restar el costo de producción. Un margen del 60% significa que de cada 45 MXN que cobras, 27 MXN son ganancia bruta.
- **Margen bruto absoluto (MXN):** Ganancia en pesos por cada unidad vendida.

### Punto de equilibrio

- El número mínimo de unidades que necesitas vender en un mes para cubrir tus costos fijos (renta, transporte, marketing). Debajo de ese número, pierdes dinero.

### Proyecciones

- Basadas en promedio móvil de los meses registrados. Con solo 3 meses de datos la confianza es **baja** — las proyecciones mejorarán a medida que acumules más historial.

---

## 6. Errores Comunes y Cómo Resolverlos

| Mensaje del agente | Qué significa | Qué hacer |
|---|---|---|
| "No tengo un sabor llamado 'uva' en tu catálogo" | Escribiste un sabor que no existe | Usar: mango, fresa, limon, jengibre o menta |
| "Para registrar la venta necesito: cantidad, presentación..." | Falta información en tu mensaje | Agregar los datos que pide |
| "No puedo acceder a tus datos en este momento" | Error temporal de conexión con Google Sheets | Esperar unos minutos y reintentar |
| "No pude completar el análisis en los pasos disponibles" | La pregunta es demasiado compleja o ambigua | Reformular de forma más específica |
| "No tengo registrado el costo de producción de [sabor]" | Falta el costo de ese sabor en la hoja Costos | Pedir al administrador que registre los costos |

---

## 7. Buenas Prácticas

**Sé específico en tus preguntas.** "¿Cuál es el margen de mango en junio?" es mejor que "¿cómo voy?".

**Registra ventas el mismo día.** El agente usa la fecha actual si no le dices otra. Si registras una venta de ayer, especifícalo: "Registra que ayer vendí 5 de mango a 45 en el gimnasio".

**Usa el agente para verificar después de registrar.** Tras registrar una venta, pregunta "¿cuánto llevo de mango este mes?" para confirmar que se registró correctamente.

**No inventes datos para probar.** El agente registra todo lo que le digas. Si quieres probar, usa el ambiente de desarrollo local (pregunta al administrador).

---

## 8. Preguntas Frecuentes

**¿El agente puede borrar un registro?**
No. Por seguridad, el agente solo puede agregar registros, no borrar ni modificar los existentes. Si registraste algo por error, informa al administrador para que lo corrija directamente en Google Sheets.

**¿El agente recuerda conversaciones anteriores?**
Solo dentro de la misma sesión (últimos 5 mensajes). Si cierras y abres una nueva conversación, el agente empieza de cero.

**¿Puedo preguntar en inglés?**
El agente está configurado para responder en español. Puede entender inglés pero responderá en español.

**¿Cuánto tarda en responder?**
Consultas simples (ventas, registros): 2-3 segundos. Análisis complejos (resúmenes, recomendaciones): 5-12 segundos.

**¿Mis datos están seguros?**
Los datos viven en Google Sheets con acceso controlado por el administrador. El agente accede mediante una cuenta de servicio con permisos limitados (lectura de todas las hojas, escritura solo en Ventas y Gastos). Las conversaciones no se almacenan entre sesiones.
