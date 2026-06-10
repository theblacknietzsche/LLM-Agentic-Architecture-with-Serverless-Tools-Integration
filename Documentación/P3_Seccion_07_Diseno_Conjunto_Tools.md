# PROYECTO 3 – Sección 7: Diseño del Conjunto de Tools (APIs Internas Simuladas)

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 7.1 Lista Completa de Tools

El agente BrewFinance opera con 4 tools principales y 1 tool auxiliar (health check). Cada tool se expone como un endpoint REST independiente, implementado como Cloud Function en producción y como endpoint del Mock Sheets API en desarrollo.

| # | Tool | Endpoint | Método | Categoría | Modifica estado |
|---|---|---|---|---|---|
| T1 | `sheets_reader` | `/api/v1/sheets/read` | POST | Lectura de datos | No |
| T2 | `sheets_writer` | `/api/v1/sheets/write` | POST | Escritura de datos | Sí |
| T3 | `calculator` | `/api/v1/calc` | POST | Cálculo financiero | No |
| T4 | `report_generator` | `/api/v1/report` | POST | Generación de texto | No |
| T5 | `health_check` | `/health` | GET | Diagnóstico | No |

---

## 7.2 Esquema Base de Request / Response

Todos los tools comparten una estructura envolvente estándar.

### Request base

```json
{
  "request_id": "req-20260615-abc123",
  "timestamp": "2026-06-15T14:30:00Z",
  "payload": {
    // contenido específico del tool
  }
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `request_id` | string | Sí | Identificador único del request (generado por el orchestrator) |
| `timestamp` | string (ISO 8601) | Sí | Momento del request |
| `payload` | object | Sí | Cuerpo específico de cada tool |

### Response base (éxito)

```json
{
  "request_id": "req-20260615-abc123",
  "status": "success",
  "timestamp": "2026-06-15T14:30:01Z",
  "latency_ms": 342,
  "data": {
    // contenido específico del tool
  }
}
```

### Response base (error)

```json
{
  "request_id": "req-20260615-abc123",
  "status": "error",
  "timestamp": "2026-06-15T14:30:01Z",
  "latency_ms": 45,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "El campo 'cantidad' debe ser un entero positivo.",
    "field": "payload.registro.cantidad",
    "received_value": -3
  }
}
```

---

## 7.3 Tool 1: `sheets_reader` — Especificación Completa

### Endpoint
`POST /api/v1/sheets/read`

### Input Schema (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SheetsReaderRequest",
  "type": "object",
  "required": ["request_id", "timestamp", "payload"],
  "properties": {
    "request_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "payload": {
      "type": "object",
      "required": ["hoja"],
      "properties": {
        "hoja": {
          "type": "string",
          "enum": ["Ventas", "Costos", "Gastos"],
          "description": "Nombre de la hoja a consultar"
        },
        "filtros": {
          "type": "object",
          "properties": {
            "mes": {
              "type": "string",
              "pattern": "^\\d{4}-\\d{2}$",
              "description": "Filtro por mes (YYYY-MM)"
            },
            "sabor": {
              "type": "string",
              "description": "Filtro por nombre de sabor"
            },
            "canal": {
              "type": "string",
              "enum": ["gimnasio", "redes"]
            },
            "presentacion": {
              "type": "string",
              "enum": ["345ml", "1L"]
            },
            "fecha_desde": {
              "type": "string",
              "format": "date",
              "description": "Filtro por rango de fecha (inicio)"
            },
            "fecha_hasta": {
              "type": "string",
              "format": "date",
              "description": "Filtro por rango de fecha (fin)"
            }
          }
        },
        "campos": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Columnas a retornar. Si se omite, retorna todas."
        },
        "limite": {
          "type": "integer",
          "minimum": 1,
          "maximum": 500,
          "default": 100,
          "description": "Máximo de registros a retornar"
        },
        "orden": {
          "type": "object",
          "properties": {
            "campo": { "type": "string" },
            "direccion": { "type": "string", "enum": ["asc", "desc"] }
          }
        }
      }
    }
  }
}
```

### Output Schema — Hoja "Ventas"

```json
{
  "request_id": "req-20260615-abc123",
  "status": "success",
  "timestamp": "2026-06-15T14:30:01Z",
  "latency_ms": 342,
  "data": {
    "hoja": "Ventas",
    "total_registros": 3,
    "registros": [
      {
        "fila": 15,
        "fecha": "2026-06-02",
        "sabor": "mango",
        "presentacion": "345ml",
        "cantidad": 5,
        "precio_unitario": 45.00,
        "canal": "gimnasio",
        "ingreso_total": 225.00
      },
      {
        "fila": 18,
        "fecha": "2026-06-05",
        "sabor": "mango",
        "presentacion": "1L",
        "cantidad": 1,
        "precio_unitario": 90.00,
        "canal": "redes",
        "ingreso_total": 90.00
      },
      {
        "fila": 22,
        "fecha": "2026-06-10",
        "sabor": "mango",
        "presentacion": "345ml",
        "cantidad": 3,
        "precio_unitario": 45.00,
        "canal": "gimnasio",
        "ingreso_total": 135.00
      }
    ]
  }
}
```

### Output Schema — Hoja "Costos"

```json
{
  "data": {
    "hoja": "Costos",
    "total_registros": 5,
    "registros": [
      {
        "sabor": "mango",
        "costo_ingredientes": 10.00,
        "costo_envase": 4.50,
        "costo_mano_obra": 3.00,
        "costo_unitario_total": 17.50,
        "presentacion": "345ml"
      }
    ]
  }
}
```

### Output Schema — Hoja "Gastos"

```json
{
  "data": {
    "hoja": "Gastos",
    "total_registros": 2,
    "registros": [
      {
        "fila": 5,
        "fecha": "2026-06-01",
        "categoria": "envases",
        "descripcion": "Compra de botellas 345ml x100",
        "monto": 500.00
      }
    ]
  }
}
```

### Columnas válidas por hoja

| Hoja | Columnas |
|---|---|
| **Ventas** | `fecha`, `sabor`, `presentacion`, `cantidad`, `precio_unitario`, `canal`, `ingreso_total` |
| **Costos** | `sabor`, `presentacion`, `costo_ingredientes`, `costo_envase`, `costo_mano_obra`, `costo_unitario_total` |
| **Gastos** | `fecha`, `categoria`, `descripcion`, `monto` |

---

## 7.4 Tool 2: `sheets_writer` — Especificación Completa

### Endpoint
`POST /api/v1/sheets/write`

### Input Schema — Registro de venta

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SheetsWriterRequest",
  "type": "object",
  "required": ["request_id", "timestamp", "payload"],
  "properties": {
    "request_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "payload": {
      "type": "object",
      "required": ["hoja", "registro", "idempotency_key"],
      "properties": {
        "hoja": {
          "type": "string",
          "enum": ["Ventas", "Gastos"]
        },
        "registro": {
          "type": "object",
          "oneOf": [
            {
              "title": "RegistroVenta",
              "required": ["fecha", "sabor", "presentacion", "cantidad", "precio_unitario", "canal"],
              "properties": {
                "fecha": { "type": "string", "format": "date" },
                "sabor": { "type": "string" },
                "presentacion": { "type": "string", "enum": ["345ml", "1L"] },
                "cantidad": { "type": "integer", "minimum": 1, "maximum": 1000 },
                "precio_unitario": { "type": "number", "minimum": 0.01, "maximum": 500 },
                "canal": { "type": "string", "enum": ["gimnasio", "redes"] }
              }
            },
            {
              "title": "RegistroGasto",
              "required": ["fecha", "categoria", "monto"],
              "properties": {
                "fecha": { "type": "string", "format": "date" },
                "categoria": { "type": "string" },
                "descripcion": { "type": "string", "maxLength": 200 },
                "monto": { "type": "number", "minimum": 0.01, "maximum": 100000 }
              }
            }
          ]
        },
        "idempotency_key": {
          "type": "string",
          "maxLength": 100,
          "description": "Clave única para evitar inserciones duplicadas"
        }
      }
    }
  }
}
```

### Output Schema (éxito)

```json
{
  "request_id": "req-20260615-def456",
  "status": "success",
  "timestamp": "2026-06-15T14:32:00Z",
  "latency_ms": 520,
  "data": {
    "hoja": "Ventas",
    "fila_insertada": 48,
    "registro": {
      "fecha": "2026-06-15",
      "sabor": "fresa",
      "presentacion": "345ml",
      "cantidad": 8,
      "precio_unitario": 45.00,
      "canal": "gimnasio",
      "ingreso_total": 360.00
    },
    "idempotency_key": "v-20260615-fresa-345-8-45-gym",
    "duplicado": false
  }
}
```

### Categorías válidas de gastos

| Categoría | Ejemplos |
|---|---|
| `ingredientes` | Fruta, azúcar, conservantes |
| `envases` | Botellas, tapas, etiquetas |
| `transporte` | Envíos, gasolina, entregas |
| `marketing` | Publicidad en redes, material impreso |
| `operativo` | Renta, servicios, herramientas |
| `otro` | Gastos no categorizados |

---

## 7.5 Tool 3: `calculator` — Especificación Completa

### Endpoint
`POST /api/v1/calc`

### Input Schema por operación

#### Operación: `margen_por_sabor`

```json
{
  "payload": {
    "operacion": "margen_por_sabor",
    "params": {
      "ventas": [
        { "sabor": "mango", "cantidad": 12, "precio_unitario": 45.00 },
        { "sabor": "fresa", "cantidad": 10, "precio_unitario": 45.00 }
      ],
      "costos": [
        { "sabor": "mango", "costo_unitario": 17.50 },
        { "sabor": "fresa", "costo_unitario": 19.00 }
      ]
    }
  }
}
```

#### Operación: `proyeccion_ventas`

```json
{
  "payload": {
    "operacion": "proyeccion_ventas",
    "params": {
      "ventas_historicas": [
        { "mes": "2026-04", "unidades": 35 },
        { "mes": "2026-05", "unidades": 40 },
        { "mes": "2026-06", "unidades": 43 }
      ],
      "meses_a_proyectar": 3,
      "metodo": "promedio_movil"
    }
  }
}
```

#### Operación: `punto_equilibrio`

```json
{
  "payload": {
    "operacion": "punto_equilibrio",
    "params": {
      "costos_fijos_mensuales": 350.00,
      "precio_unitario": 45.00,
      "costo_unitario": 17.50
    }
  }
}
```

#### Operación: `resumen_periodo`

```json
{
  "payload": {
    "operacion": "resumen_periodo",
    "params": {
      "ventas": [ ... ],
      "costos": [ ... ],
      "gastos": [ ... ],
      "periodo": "2026-06"
    }
  }
}
```

#### Operación: `comparar_presentaciones`

```json
{
  "payload": {
    "operacion": "comparar_presentaciones",
    "params": {
      "ventas": [
        { "sabor": "mango", "presentacion": "345ml", "cantidad": 10, "precio_unitario": 45.00 },
        { "sabor": "mango", "presentacion": "1L", "cantidad": 2, "precio_unitario": 90.00 }
      ],
      "costos": [
        { "sabor": "mango", "presentacion": "345ml", "costo_unitario": 17.50 },
        { "sabor": "mango", "presentacion": "1L", "costo_unitario": 38.00 }
      ]
    }
  }
}
```

#### Operación: `margen_por_canal`

```json
{
  "payload": {
    "operacion": "margen_por_canal",
    "params": {
      "ventas": [
        { "sabor": "mango", "canal": "gimnasio", "cantidad": 8, "precio_unitario": 45.00 },
        { "sabor": "mango", "canal": "redes", "cantidad": 4, "precio_unitario": 45.00 }
      ],
      "costos": [
        { "sabor": "mango", "costo_unitario": 17.50 }
      ]
    }
  }
}
```

### Output Schema — `proyeccion_ventas`

```json
{
  "data": {
    "operacion": "proyeccion_ventas",
    "resultado": {
      "metodo": "promedio_movil",
      "datos_historicos": [35, 40, 43],
      "tendencia": "creciente",
      "proyecciones": [
        { "mes": "2026-07", "unidades_estimadas": 42 },
        { "mes": "2026-08", "unidades_estimadas": 42 },
        { "mes": "2026-09", "unidades_estimadas": 42 }
      ],
      "confianza": "baja",
      "nota": "Proyección basada en solo 3 meses de datos. Confianza aumentará con más historial."
    },
    "metadata": {
      "moneda": "MXN",
      "meses_historicos": 3
    }
  }
}
```

### Output Schema — `punto_equilibrio`

```json
{
  "data": {
    "operacion": "punto_equilibrio",
    "resultado": {
      "unidades_equilibrio": 13,
      "ingreso_equilibrio": 585.00,
      "margen_contribucion_unitario": 27.50,
      "interpretacion": "Necesitas vender al menos 13 unidades al mes para cubrir los costos fijos de $350."
    }
  }
}
```

---

## 7.6 Tool 4: `report_generator` — Especificación Completa

### Endpoint
`POST /api/v1/report`

### Input Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReportGeneratorRequest",
  "type": "object",
  "required": ["request_id", "timestamp", "payload"],
  "properties": {
    "request_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "payload": {
      "type": "object",
      "required": ["tipo_reporte", "datos"],
      "properties": {
        "tipo_reporte": {
          "type": "string",
          "enum": ["resumen_mensual", "comparativa_sabores", "recomendacion_precio", "analisis_canal"]
        },
        "datos": {
          "type": "object",
          "description": "Datos pre-calculados por el tool calculator"
        },
        "idioma": {
          "type": "string",
          "default": "es",
          "enum": ["es"]
        }
      }
    }
  }
}
```

### Output Schema — `recomendacion_precio`

```json
{
  "data": {
    "tipo_reporte": "recomendacion_precio",
    "reporte": {
      "titulo": "Recomendación de Precio — Limón 345ml",
      "sabor": "limon",
      "presentacion": "345ml",
      "precio_actual": 40.00,
      "precio_sugerido": 45.00,
      "secciones": [
        {
          "subtitulo": "Situación actual",
          "contenido": "Limón 345ml se vende a $40 con un costo de producción de $15.80, lo que genera un margen bruto de 60.5% ($24.20 por unidad). Es tu 3er sabor en volumen de ventas (8 unidades/mes)."
        },
        {
          "subtitulo": "Análisis del ajuste",
          "contenido": "Un incremento de $5 (de $40 a $45) elevaría el margen a 64.9% ($29.20 por unidad). Considerando que los demás sabores ya se venden a $45, el ajuste homogeneiza los precios y simplifica la operación."
        },
        {
          "subtitulo": "Riesgo estimado",
          "contenido": "Limón es tu 3er sabor en ventas. Un incremento del 12.5% en precio tiene riesgo bajo de afectar el volumen, especialmente en el canal gimnasio donde la compra es por conveniencia."
        },
        {
          "subtitulo": "Recomendación",
          "contenido": "Subir el precio de limón 345ml de $40 a $45. Impacto estimado: +$38.40/mes en margen adicional (asumiendo el mismo volumen de 8 unidades)."
        }
      ]
    }
  }
}
```

---

## 7.7 Catálogo Unificado de Códigos de Error

| Código | HTTP | Tool(s) | Descripción | Acción del agente |
|---|---|---|---|---|
| `SHEET_NOT_FOUND` | 404 | reader | La hoja solicitada no existe | Informar hojas válidas |
| `INVALID_FILTER` | 400 | reader | Campo de filtro no existe en la hoja | Listar campos válidos |
| `EMPTY_RESULT` | 200 | reader | Consulta sin resultados (no es fallo) | Informar al usuario, sugerir ajustar filtros |
| `VALIDATION_FAILED` | 400 | writer | Campo con valor fuera de rango o tipo incorrecto | Informar campo, regla y valor recibido |
| `INVALID_SHEET` | 400 | writer | Se intentó escribir en hoja de solo lectura | Informar que Costos es solo lectura |
| `UNKNOWN_SABOR` | 400 | writer | Sabor no existe en catálogo | Listar los 5 sabores válidos |
| `UNKNOWN_CANAL` | 400 | writer | Canal no reconocido | Informar canales válidos: gimnasio, redes |
| `DUPLICATE_DETECTED` | 200 | writer | El idempotency_key ya existe | Informar sin insertar duplicado |
| `UNKNOWN_OPERATION` | 400 | calculator | Operación no soportada | Listar operaciones válidas |
| `MISSING_PARAMS` | 400 | calculator | Faltan parámetros para la operación | Indicar qué parámetros faltan |
| `INVALID_DATA` | 400 | calculator | Datos con formato incorrecto | Describir el formato esperado |
| `DIVISION_BY_ZERO` | 422 | calculator | Cálculo con denominador cero | Informar, sugerir verificar datos |
| `INSUFFICIENT_DATA` | 422 | calculator | Datos insuficientes para el cálculo | Informar mínimo requerido |
| `UNKNOWN_REPORT_TYPE` | 400 | report_gen | Tipo de reporte no soportado | Listar tipos válidos |
| `MISSING_DATA` | 400 | report_gen | Faltan campos requeridos en datos | Indicar campos faltantes |
| `INVALID_DATA_FORMAT` | 400 | report_gen | Valores con formato incorrecto | Describir formato esperado |
| `SHEETS_API_ERROR` | 502 | reader, writer | Error de conexión con Google Sheets API | Pedir al usuario que reintente |
| `AUTH_ERROR` | 401 | reader, writer | Credenciales inválidas o expiradas | Error interno, notificar al admin |
| `RATE_LIMIT` | 429 | reader, writer | Cuota de Sheets API excedida | Esperar y reintentar automáticamente |
| `INTERNAL_ERROR` | 500 | todos | Error no anticipado | Registrar en logs, informar al usuario |

---

## 7.8 Datos del Mock API para Desarrollo

El Mock Sheets API (`mock-sheets-api` del Docker Compose, Sección 4) pre-carga datos de prueba que simulan 3 meses de operación real.

### Dataset: Ventas (muestra)

| fecha | sabor | presentacion | cantidad | precio_unitario | canal |
|---|---|---|---|---|---|
| 2026-04-05 | mango | 345ml | 4 | 45.00 | gimnasio |
| 2026-04-08 | fresa | 345ml | 3 | 45.00 | redes |
| 2026-04-12 | limon | 345ml | 2 | 40.00 | gimnasio |
| 2026-04-15 | mango | 1L | 1 | 90.00 | redes |
| 2026-05-03 | jengibre | 345ml | 5 | 50.00 | gimnasio |
| 2026-05-10 | menta | 345ml | 3 | 45.00 | gimnasio |
| ... | ... | ... | ... | ... | ... |

### Dataset: Costos

| sabor | presentacion | costo_ingredientes | costo_envase | costo_mano_obra | costo_unitario_total |
|---|---|---|---|---|---|
| mango | 345ml | 10.00 | 4.50 | 3.00 | 17.50 |
| fresa | 345ml | 11.50 | 4.50 | 3.00 | 19.00 |
| limon | 345ml | 8.80 | 4.00 | 3.00 | 15.80 |
| jengibre | 345ml | 13.00 | 4.50 | 3.00 | 20.50 |
| menta | 345ml | 9.50 | 4.50 | 3.00 | 17.00 |
| mango | 1L | 22.00 | 10.00 | 6.00 | 38.00 |
| fresa | 1L | 25.00 | 10.00 | 6.00 | 41.00 |

### Dataset: Gastos (muestra)

| fecha | categoria | descripcion | monto |
|---|---|---|---|
| 2026-06-01 | envases | Botellas 345ml x100 | 500.00 |
| 2026-06-05 | ingredientes | Fruta de temporada | 320.00 |
| 2026-06-10 | transporte | Entrega al gimnasio | 80.00 |
| 2026-06-15 | marketing | Promoción en Instagram | 150.00 |
