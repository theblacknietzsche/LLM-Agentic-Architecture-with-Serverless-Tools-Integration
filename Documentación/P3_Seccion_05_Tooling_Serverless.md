# PROYECTO 3 – Sección 5: Tooling Serverless (Google Cloud Functions)

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 5.1 Inventario de Tools Serverless

Cada tool del agente BrewFinance se implementa como una **Cloud Function (2nd gen)** independiente en Google Cloud. El agente orquestador invoca estas funciones vía HTTP durante el ciclo ReAct.

| # | Tool | Cloud Function | Runtime | Trigger | Descripción |
|---|---|---|---|---|---|
| T1 | `sheets_reader` | `bf-sheets-reader` | Python 3.12 | HTTP | Lee datos de ventas, costos o gastos desde Google Sheets |
| T2 | `sheets_writer` | `bf-sheets-writer` | Python 3.12 | HTTP | Registra nuevas filas de ventas o gastos en Google Sheets |
| T3 | `calculator` | `bf-calculator` | Python 3.12 | HTTP | Ejecuta cálculos financieros (márgenes, proyecciones, punto de equilibrio) |
| T4 | `report_generator` | `bf-report-generator` | Python 3.12 | HTTP | Genera resúmenes financieros estructurados a partir de datos procesados |

---

## 5.2 Tool 1: `sheets_reader`

### Propósito
Leer datos filtrados desde una hoja específica del Google Sheets del negocio (Ventas, Costos o Gastos).

### Contrato JSON — Input

```json
{
  "hoja": "Ventas",
  "filtros": {
    "mes": "2026-06",
    "sabor": "mango"
  },
  "campos": ["sabor", "presentacion", "cantidad", "precio_unitario", "canal", "fecha"]
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `hoja` | string | Sí | Nombre de la hoja: `"Ventas"`, `"Costos"` o `"Gastos"` |
| `filtros` | object | No | Filtros opcionales. Claves válidas dependen de la hoja |
| `campos` | array[string] | No | Columnas a retornar. Si se omite, retorna todas |

### Contrato JSON — Output (éxito)

```json
{
  "status": "success",
  "hoja": "Ventas",
  "total_registros": 12,
  "data": [
    {
      "sabor": "mango",
      "presentacion": "345ml",
      "cantidad": 5,
      "precio_unitario": 45.00,
      "canal": "gimnasio",
      "fecha": "2026-06-02"
    },
    {
      "sabor": "mango",
      "presentacion": "345ml",
      "cantidad": 3,
      "precio_unitario": 45.00,
      "canal": "redes",
      "fecha": "2026-06-10"
    }
  ]
}
```

### Contrato JSON — Output (error)

```json
{
  "status": "error",
  "error_code": "SHEET_NOT_FOUND",
  "message": "La hoja 'Inventario' no existe. Hojas válidas: Ventas, Costos, Gastos."
}
```

### Códigos de error

| Código | HTTP | Descripción |
|---|---|---|
| `SHEET_NOT_FOUND` | 404 | La hoja solicitada no existe en el spreadsheet |
| `INVALID_FILTER` | 400 | El filtro contiene campos que no existen en la hoja |
| `EMPTY_RESULT` | 200 | La consulta no retorna registros (no es un error, pero se informa) |
| `SHEETS_API_ERROR` | 502 | Error de conexión con la API de Google Sheets |
| `AUTH_ERROR` | 401 | Credenciales de servicio inválidas o expiradas |
| `RATE_LIMIT` | 429 | Se excedió la cuota de la API de Sheets (300 req/min) |

### Idempotencia

`sheets_reader` es **naturalmente idempotente**: invocarla N veces con los mismos parámetros retorna el mismo resultado (asumiendo que los datos no cambian entre llamadas). No modifica estado.

---

## 5.3 Tool 2: `sheets_writer`

### Propósito
Registrar una nueva fila de venta o gasto en la hoja correspondiente de Google Sheets.

### Contrato JSON — Input

```json
{
  "hoja": "Ventas",
  "registro": {
    "fecha": "2026-06-15",
    "sabor": "fresa",
    "presentacion": "345ml",
    "cantidad": 8,
    "precio_unitario": 45.00,
    "canal": "gimnasio"
  },
  "idempotency_key": "venta-20260615-fresa-345-8-45-gym"
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `hoja` | string | Sí | `"Ventas"` o `"Gastos"` (Costos es solo lectura) |
| `registro` | object | Sí | Datos de la fila a insertar |
| `idempotency_key` | string | Sí | Clave única para evitar duplicados |

### Contrato JSON — Output (éxito)

```json
{
  "status": "success",
  "hoja": "Ventas",
  "fila_insertada": 47,
  "registro": {
    "fecha": "2026-06-15",
    "sabor": "fresa",
    "presentacion": "345ml",
    "cantidad": 8,
    "precio_unitario": 45.00,
    "canal": "gimnasio"
  },
  "idempotency_key": "venta-20260615-fresa-345-8-45-gym",
  "duplicado": false
}
```

### Contrato JSON — Output (duplicado detectado)

```json
{
  "status": "success",
  "hoja": "Ventas",
  "fila_insertada": 47,
  "registro": { ... },
  "idempotency_key": "venta-20260615-fresa-345-8-45-gym",
  "duplicado": true,
  "message": "Este registro ya fue insertado previamente. No se creó un duplicado."
}
```

### Contrato JSON — Output (error)

```json
{
  "status": "error",
  "error_code": "VALIDATION_FAILED",
  "message": "El campo 'cantidad' debe ser un entero positivo. Valor recibido: -3"
}
```

### Códigos de error

| Código | HTTP | Descripción |
|---|---|---|
| `VALIDATION_FAILED` | 400 | Uno o más campos no pasan validación (rango, tipo, formato) |
| `INVALID_SHEET` | 400 | Se intentó escribir en `"Costos"` (solo lectura) o hoja inexistente |
| `UNKNOWN_SABOR` | 400 | El sabor no existe en el catálogo de 5 sabores |
| `UNKNOWN_CANAL` | 400 | El canal no es `"gimnasio"` ni `"redes"` |
| `DUPLICATE_DETECTED` | 200 | El `idempotency_key` ya existe — retorna éxito sin insertar |
| `SHEETS_API_ERROR` | 502 | Error de conexión con Google Sheets |
| `AUTH_ERROR` | 401 | Credenciales de servicio inválidas o expiradas |

### Idempotencia

`sheets_writer` implementa **idempotencia explícita** mediante el campo `idempotency_key`:

1. Antes de insertar, la función busca si el `idempotency_key` ya existe en una columna oculta de la hoja
2. Si existe → retorna `"duplicado": true` sin insertar una nueva fila
3. Si no existe → inserta la fila y registra el key

Esto protege contra reintentos del agente (si un tool call falla por timeout y el ciclo ReAct lo reintenta) y contra duplicados accidentales del usuario ("Registra 5 de mango" enviado dos veces).

### Reglas de validación (Guardrail integrado)

| Campo | Regla | Mensaje de error |
|---|---|---|
| `cantidad` | Entero positivo, ≤ 1,000 | "cantidad debe ser entero positivo ≤ 1,000" |
| `precio_unitario` | Número > 0, ≤ 500 | "precio_unitario debe ser > 0 y ≤ 500" |
| `sabor` | Debe existir en catálogo | "Sabor '[x]' no reconocido. Válidos: [lista]" |
| `presentacion` | `"345ml"` o `"1L"` | "Presentación debe ser '345ml' o '1L'" |
| `canal` | `"gimnasio"` o `"redes"` | "Canal debe ser 'gimnasio' o 'redes'" |
| `fecha` | Formato ISO 8601, no futura | "Fecha inválida o futura" |

---

## 5.4 Tool 3: `calculator`

### Propósito
Ejecutar cálculos financieros sobre datos ya obtenidos. El LLM no debe hacer aritmética por sí solo — siempre delega a esta función para evitar errores de cálculo.

### Contrato JSON — Input

```json
{
  "operacion": "margen_por_sabor",
  "params": {
    "ventas": [
      {"sabor": "mango", "cantidad": 12, "precio_unitario": 45.00},
      {"sabor": "fresa", "cantidad": 10, "precio_unitario": 45.00},
      {"sabor": "limon", "cantidad": 8, "precio_unitario": 40.00}
    ],
    "costos": [
      {"sabor": "mango", "costo_unitario": 17.50},
      {"sabor": "fresa", "costo_unitario": 19.00},
      {"sabor": "limon", "costo_unitario": 15.80}
    ]
  }
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `operacion` | string | Sí | Tipo de cálculo a ejecutar |
| `params` | object | Sí | Datos de entrada para el cálculo (estructura varía por operación) |

### Operaciones soportadas

| Operación | Descripción | Params requeridos |
|---|---|---|
| `margen_por_sabor` | Calcula margen bruto (%) y absoluto ($) por sabor | `ventas`, `costos` |
| `margen_por_canal` | Calcula margen bruto por canal de venta | `ventas`, `costos` |
| `proyeccion_ventas` | Proyecta ventas a N meses usando promedio móvil | `ventas_historicas`, `meses_a_proyectar` |
| `punto_equilibrio` | Calcula unidades necesarias para cubrir costos fijos | `costos_fijos`, `precio_unitario`, `costo_unitario` |
| `resumen_periodo` | Calcula totales de ingresos, costos y margen para un periodo | `ventas`, `costos`, `gastos` |
| `comparar_presentaciones` | Compara rentabilidad entre 345ml y 1L | `ventas`, `costos` |

### Contrato JSON — Output (éxito)

```json
{
  "status": "success",
  "operacion": "margen_por_sabor",
  "resultado": [
    {
      "sabor": "mango",
      "ingresos": 540.00,
      "costo_total": 210.00,
      "margen_absoluto": 330.00,
      "margen_porcentaje": 61.11,
      "unidades_vendidas": 12
    },
    {
      "sabor": "fresa",
      "ingresos": 450.00,
      "costo_total": 190.00,
      "margen_absoluto": 260.00,
      "margen_porcentaje": 57.78,
      "unidades_vendidas": 10
    },
    {
      "sabor": "limon",
      "ingresos": 320.00,
      "costo_total": 126.40,
      "margen_absoluto": 193.60,
      "margen_porcentaje": 60.50,
      "unidades_vendidas": 8
    }
  ],
  "metadata": {
    "moneda": "MXN",
    "periodo": "2026-06"
  }
}
```

### Contrato JSON — Output (error)

```json
{
  "status": "error",
  "error_code": "UNKNOWN_OPERATION",
  "message": "La operación 'roi_proyectado' no está soportada. Operaciones válidas: margen_por_sabor, margen_por_canal, proyeccion_ventas, punto_equilibrio, resumen_periodo, comparar_presentaciones."
}
```

### Códigos de error

| Código | HTTP | Descripción |
|---|---|---|
| `UNKNOWN_OPERATION` | 400 | La operación solicitada no existe |
| `MISSING_PARAMS` | 400 | Faltan parámetros requeridos para la operación |
| `INVALID_DATA` | 400 | Los datos de entrada tienen formato incorrecto o valores inválidos |
| `DIVISION_BY_ZERO` | 422 | Un cálculo resultaría en división por cero (ej: costo = 0) |
| `INSUFFICIENT_DATA` | 422 | No hay suficientes datos para el cálculo (ej: proyección con < 2 meses) |

### Idempotencia

`calculator` es **naturalmente idempotente**: es una función pura sin estado. Los mismos inputs siempre producen los mismos outputs. No lee ni escribe datos externos.

---

## 5.5 Tool 4: `report_generator`

### Propósito
Generar un resumen financiero estructurado en texto a partir de datos ya calculados. Formatea los resultados del `calculator` en una narrativa lista para presentar al usuario.

### Contrato JSON — Input

```json
{
  "tipo_reporte": "resumen_mensual",
  "datos": {
    "periodo": "2026-06",
    "ingresos_totales": 1810.00,
    "costos_totales": 726.40,
    "gastos_operativos": 350.00,
    "margen_bruto": 1083.60,
    "margen_bruto_pct": 59.87,
    "mejor_sabor": {"sabor": "mango", "margen_pct": 61.11},
    "peor_sabor": {"sabor": "fresa", "margen_pct": 57.78},
    "canal_principal": {"canal": "gimnasio", "porcentaje_volumen": 78},
    "unidades_totales": 43
  }
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `tipo_reporte` | string | Sí | Tipo de reporte a generar |
| `datos` | object | Sí | Datos financieros pre-calculados |

### Tipos de reporte soportados

| Tipo | Descripción |
|---|---|
| `resumen_mensual` | Resumen financiero completo del mes |
| `comparativa_sabores` | Ranking de sabores por rentabilidad |
| `recomendacion_precio` | Análisis y recomendación de ajuste de precio para un sabor |
| `analisis_canal` | Comparación de desempeño entre canales de venta |

### Contrato JSON — Output (éxito)

```json
{
  "status": "success",
  "tipo_reporte": "resumen_mensual",
  "reporte": {
    "titulo": "Resumen Financiero — Junio 2026",
    "secciones": [
      {
        "subtitulo": "Resultados generales",
        "contenido": "En junio vendiste 43 unidades con ingresos de $1,810 MXN. Tus costos de producción fueron $726.40 y los gastos operativos $350, dejando un margen bruto de $1,083.60 (59.87%)."
      },
      {
        "subtitulo": "Sabores destacados",
        "contenido": "Tu sabor más rentable fue mango (61.11% de margen). El de menor margen fue fresa (57.78%), aunque la diferencia es pequeña."
      },
      {
        "subtitulo": "Canales de venta",
        "contenido": "El gimnasio representó el 78% de tu volumen de ventas. Las ventas por redes sociales aún son un canal secundario."
      }
    ]
  }
}
```

### Códigos de error

| Código | HTTP | Descripción |
|---|---|---|
| `UNKNOWN_REPORT_TYPE` | 400 | El tipo de reporte no está soportado |
| `MISSING_DATA` | 400 | Faltan campos requeridos en el objeto `datos` |
| `INVALID_DATA_FORMAT` | 400 | Los valores en `datos` no tienen el formato esperado |

### Idempotencia

`report_generator` es **naturalmente idempotente**: los mismos datos de entrada siempre producen el mismo reporte. No tiene estado ni efectos secundarios.

---

## 5.6 Registro de Tools para el LLM (Function Declarations)

Cada tool se registra como un `function_declaration` en el parámetro `tools` de la API de Gemini. Esto permite que el modelo decida autónomamente cuándo invocar cada función.

```json
{
  "tools": [
    {
      "function_declarations": [
        {
          "name": "sheets_reader",
          "description": "Lee datos de ventas, costos o gastos desde Google Sheets. Usar siempre que se necesite consultar información financiera del negocio.",
          "parameters": {
            "type": "object",
            "properties": {
              "hoja": {
                "type": "string",
                "description": "Hoja a consultar: 'Ventas', 'Costos' o 'Gastos'",
                "enum": ["Ventas", "Costos", "Gastos"]
              },
              "filtros": {
                "type": "object",
                "description": "Filtros opcionales (mes, sabor, canal, presentacion)",
                "properties": {
                  "mes": {"type": "string", "description": "Mes en formato YYYY-MM"},
                  "sabor": {"type": "string"},
                  "canal": {"type": "string", "enum": ["gimnasio", "redes"]},
                  "presentacion": {"type": "string", "enum": ["345ml", "1L"]}
                }
              },
              "campos": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Columnas a retornar. Si se omite, retorna todas."
              }
            },
            "required": ["hoja"]
          }
        },
        {
          "name": "sheets_writer",
          "description": "Registra una nueva venta o gasto en Google Sheets. Usar cuando el usuario quiere agregar un registro nuevo. NUNCA inventar datos: solo registrar lo que el usuario indica explícitamente.",
          "parameters": {
            "type": "object",
            "properties": {
              "hoja": {
                "type": "string",
                "description": "Hoja destino: 'Ventas' o 'Gastos'. La hoja 'Costos' es solo lectura.",
                "enum": ["Ventas", "Gastos"]
              },
              "registro": {
                "type": "object",
                "description": "Datos de la fila a insertar",
                "properties": {
                  "fecha": {"type": "string", "description": "Fecha ISO 8601 (YYYY-MM-DD)"},
                  "sabor": {"type": "string"},
                  "presentacion": {"type": "string", "enum": ["345ml", "1L"]},
                  "cantidad": {"type": "integer", "minimum": 1},
                  "precio_unitario": {"type": "number", "minimum": 0.01},
                  "canal": {"type": "string", "enum": ["gimnasio", "redes"]},
                  "categoria": {"type": "string", "description": "Solo para gastos: categoría del gasto"},
                  "monto": {"type": "number", "description": "Solo para gastos: monto total"}
                }
              },
              "idempotency_key": {
                "type": "string",
                "description": "Clave única para evitar duplicados. Generar combinando fecha+sabor+cantidad+canal."
              }
            },
            "required": ["hoja", "registro", "idempotency_key"]
          }
        },
        {
          "name": "calculator",
          "description": "Ejecuta cálculos financieros. SIEMPRE usar esta herramienta para operaciones aritméticas — nunca calcular mentalmente. Soporta: margen_por_sabor, margen_por_canal, proyeccion_ventas, punto_equilibrio, resumen_periodo, comparar_presentaciones.",
          "parameters": {
            "type": "object",
            "properties": {
              "operacion": {
                "type": "string",
                "description": "Tipo de cálculo",
                "enum": ["margen_por_sabor", "margen_por_canal", "proyeccion_ventas", "punto_equilibrio", "resumen_periodo", "comparar_presentaciones"]
              },
              "params": {
                "type": "object",
                "description": "Datos de entrada para el cálculo. Estructura varía según la operación."
              }
            },
            "required": ["operacion", "params"]
          }
        },
        {
          "name": "report_generator",
          "description": "Genera un resumen financiero estructurado a partir de datos ya calculados. Usar DESPUÉS de calculator cuando el usuario pide un resumen, reporte o recomendación detallada.",
          "parameters": {
            "type": "object",
            "properties": {
              "tipo_reporte": {
                "type": "string",
                "description": "Tipo de reporte",
                "enum": ["resumen_mensual", "comparativa_sabores", "recomendacion_precio", "analisis_canal"]
              },
              "datos": {
                "type": "object",
                "description": "Datos financieros pre-calculados por el tool calculator."
              }
            },
            "required": ["tipo_reporte", "datos"]
          }
        }
      ]
    }
  ]
}
```

---

## 5.7 Resumen de Cumplimiento de Requisitos

| Requisito | sheets_reader | sheets_writer | calculator | report_generator |
|---|---|---|---|---|
| Contrato JSON input/output | ✅ | ✅ | ✅ | ✅ |
| Manejo de errores con códigos | ✅ (6 códigos) | ✅ (7 códigos) | ✅ (5 códigos) | ✅ (3 códigos) |
| Idempotente | ✅ (natural) | ✅ (via idempotency_key) | ✅ (natural) | ✅ (natural) |
| Registrada como tool para el LLM | ✅ | ✅ | ✅ | ✅ |
| Serverless (Cloud Function) | ✅ | ✅ | ✅ | ✅ |
