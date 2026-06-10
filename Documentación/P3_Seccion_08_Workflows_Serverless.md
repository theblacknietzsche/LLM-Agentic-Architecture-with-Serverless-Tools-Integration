# PROYECTO 3 – Sección 8: Administración de Workflows (Google Workflows)

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 8.1 Workflows del Sistema

El agente BrewFinance utiliza **Google Workflows** para orquestar flujos multi-paso que van más allá de un ciclo ReAct individual. Estos workflows coordinan llamadas secuenciales a los tools serverless con lógica condicional, manejo de errores y reintentos.

| # | Workflow | Trigger | Frecuencia | Pasos | Propósito |
|---|---|---|---|---|---|
| WF1 | `post_write_check` | HTTP (orchestrator tras `sheets_writer`) | Por cada registro nuevo | 4 | Verificar acumulados y detectar alertas tras cada escritura |
| WF2 | `weekly_summary` | Cloud Scheduler (lunes 9:00 AM) | Semanal | 5 | Generar resumen semanal automático |
| WF3 | `low_margin_alert` | Subworkflow (invocado por WF1) | Condicional | 3 | Notificar cuando el margen de un sabor cae bajo 40% |

---

## 8.2 Workflow 1: `post_write_check`

### Propósito
Cada vez que el agente registra una venta o gasto nuevo (via `sheets_writer`), este workflow se dispara para recalcular acumulados del mes y detectar si algún sabor tiene margen por debajo del umbral de alerta (40%).

### Diagrama

```
┌─────────────────────┐
│   ORCHESTRATOR       │
│  (tras sheets_writer)│
└──────────┬──────────┘
           │ HTTP POST (async)
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  WORKFLOW: post_write_check                                      │
│                                                                  │
│  ┌────────────────────────────────┐                              │
│  │ PASO 1: read_monthly_sales     │                              │
│  │ Llama: bf-sheets-reader        │                              │
│  │ Params: hoja=Ventas,           │                              │
│  │         filtro=mes actual      │                              │
│  └──────────────┬─────────────────┘                              │
│                 │                                                 │
│                 ▼                                                 │
│  ┌────────────────────────────────┐                              │
│  │ PASO 2: read_costs             │                              │
│  │ Llama: bf-sheets-reader        │                              │
│  │ Params: hoja=Costos            │                              │
│  └──────────────┬─────────────────┘                              │
│                 │                                                 │
│                 ▼                                                 │
│  ┌────────────────────────────────┐                              │
│  │ PASO 3: calculate_margins      │                              │
│  │ Llama: bf-calculator           │                              │
│  │ Params: operacion=             │                              │
│  │   margen_por_sabor             │                              │
│  └──────────────┬─────────────────┘                              │
│                 │                                                 │
│                 ▼                                                 │
│  ┌────────────────────────────────┐                              │
│  │ PASO 4: evaluate_alerts        │                              │
│  │                                │                              │
│  │ ¿Algún sabor con margen < 40%? │                              │
│  │                                │                              │
│  │   SÍ ──► Llama subworkflow:   │                              │
│  │          low_margin_alert       │                              │
│  │                                │                              │
│  │   NO ──► Fin (sin alerta)     │                              │
│  └────────────────────────────────┘                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Definición en Google Workflows (YAML)

```yaml
main:
  params: [input]
  steps:
    - init:
        assign:
          - mes_actual: ${text.substring(time.format(sys.now(), "America/Mexico_City"), 0, 7)}
          - base_url: ${sys.get_env("TOOLS_BASE_URL")}
          - umbral_margen: 40

    - read_monthly_sales:
        try:
          call: http.post
          args:
            url: ${base_url + "/api/v1/sheets/read"}
            headers:
              Content-Type: "application/json"
            body:
              request_id: ${"wf1-sales-" + string(sys.now())}
              timestamp: ${time.format(sys.now())}
              payload:
                hoja: "Ventas"
                filtros:
                  mes: ${mes_actual}
          result: sales_response
        retry:
          predicate: ${default_retry_predicate}
          max_retries: 3
          backoff:
            initial_delay: 2
            max_delay: 30
            multiplier: 2

    - read_costs:
        try:
          call: http.post
          args:
            url: ${base_url + "/api/v1/sheets/read"}
            headers:
              Content-Type: "application/json"
            body:
              request_id: ${"wf1-costs-" + string(sys.now())}
              timestamp: ${time.format(sys.now())}
              payload:
                hoja: "Costos"
          result: costs_response
        retry:
          predicate: ${default_retry_predicate}
          max_retries: 3
          backoff:
            initial_delay: 2
            max_delay: 30
            multiplier: 2

    - calculate_margins:
        try:
          call: http.post
          args:
            url: ${base_url + "/api/v1/calc"}
            headers:
              Content-Type: "application/json"
            body:
              request_id: ${"wf1-calc-" + string(sys.now())}
              timestamp: ${time.format(sys.now())}
              payload:
                operacion: "margen_por_sabor"
                params:
                  ventas: ${sales_response.body.data.registros}
                  costos: ${costs_response.body.data.registros}
          result: margin_response
        retry:
          predicate: ${default_retry_predicate}
          max_retries: 2
          backoff:
            initial_delay: 1
            max_delay: 10
            multiplier: 2

    - evaluate_alerts:
        switch:
          - condition: ${check_low_margins(margin_response.body.data.resultado, umbral_margen)}
            steps:
              - trigger_alert:
                  call: googleapis.workflowexecutions.v1.projects.locations.workflows.executions.run
                  args:
                    workflow_id: "low-margin-alert"
                    argument:
                      margenes: ${margin_response.body.data.resultado}
                      umbral: ${umbral_margen}
                      mes: ${mes_actual}
                  result: alert_result
              - return_with_alert:
                  return:
                    status: "completed_with_alert"
                    alert_triggered: true
                    margenes: ${margin_response.body.data.resultado}
        next: return_no_alert

    - return_no_alert:
        return:
          status: "completed"
          alert_triggered: false
          margenes: ${margin_response.body.data.resultado}

default_retry_predicate:
  params: [e]
  steps:
    - check_retryable:
        switch:
          - condition: ${e.code == 429 or e.code == 502 or e.code == 503}
            return: true
        next: not_retryable
    - not_retryable:
        return: false
```

---

## 8.3 Workflow 2: `weekly_summary`

### Propósito
Todos los lunes a las 9:00 AM (hora de México), este workflow genera automáticamente un resumen financiero de la semana anterior y lo almacena como un registro en una hoja dedicada de Google Sheets ("Reportes").

### Diagrama

```
┌──────────────────────┐
│   CLOUD SCHEDULER     │
│  (lunes 9:00 AM CST)  │
└──────────┬───────────┘
           │ HTTP POST
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  WORKFLOW: weekly_summary                                        │
│                                                                  │
│  ┌────────────────────────────────┐                              │
│  │ PASO 1: calculate_date_range   │                              │
│  │ Calcula: lunes anterior →      │                              │
│  │          domingo anterior      │                              │
│  └──────────────┬─────────────────┘                              │
│                 │                                                 │
│                 ▼                                                 │
│  ┌────────────────────────────────┐                              │
│  │ PASO 2: read_weekly_sales      │                              │
│  │ Llama: bf-sheets-reader        │                              │
│  │ Params: hoja=Ventas,           │                              │
│  │   filtro=fecha_desde/hasta     │                              │
│  └──────────────┬─────────────────┘                              │
│                 │                                                 │
│                 ▼                                                 │
│  ┌────────────────────────────────┐                              │
│  │ PASO 3: read_weekly_expenses   │                              │
│  │ Llama: bf-sheets-reader        │                              │
│  │ Params: hoja=Gastos,           │                              │
│  │   filtro=fecha_desde/hasta     │                              │
│  └──────────────┬─────────────────┘                              │
│                 │                                                 │
│                 ▼                                                 │
│  ┌────────────────────────────────┐                              │
│  │ PASO 4: generate_summary       │                              │
│  │ Llama: bf-calculator           │                              │
│  │ Params: operacion=             │                              │
│  │   resumen_periodo              │                              │
│  └──────────────┬─────────────────┘                              │
│                 │                                                 │
│                 ▼                                                 │
│  ┌────────────────────────────────┐                              │
│  │ PASO 5: store_report           │                              │
│  │ Llama: bf-sheets-writer        │                              │
│  │ Params: hoja=Gastos            │                              │
│  │   (registro de tipo reporte)   │                              │
│  │                                │                              │
│  │ Almacena resumen como registro │                              │
│  │ consultable por el agente      │                              │
│  └────────────────────────────────┘                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Definición en Google Workflows (YAML)

```yaml
main:
  steps:
    - init:
        assign:
          - base_url: ${sys.get_env("TOOLS_BASE_URL")}
          - today: ${time.format(sys.now(), "America/Mexico_City")}

    - calculate_date_range:
        assign:
          - week_end: ${text.substring(today, 0, 10)}
          - week_start: ${time.format(time.parse(today) - duration("168h"))}

    - read_weekly_sales:
        try:
          call: http.post
          args:
            url: ${base_url + "/api/v1/sheets/read"}
            headers:
              Content-Type: "application/json"
            body:
              request_id: ${"wf2-sales-" + week_start}
              timestamp: ${today}
              payload:
                hoja: "Ventas"
                filtros:
                  fecha_desde: ${text.substring(week_start, 0, 10)}
                  fecha_hasta: ${week_end}
          result: sales_response
        retry:
          predicate: ${default_retry_predicate}
          max_retries: 3
          backoff:
            initial_delay: 5
            max_delay: 60
            multiplier: 2

    - read_weekly_expenses:
        try:
          call: http.post
          args:
            url: ${base_url + "/api/v1/sheets/read"}
            headers:
              Content-Type: "application/json"
            body:
              request_id: ${"wf2-gastos-" + week_start}
              timestamp: ${today}
              payload:
                hoja: "Gastos"
                filtros:
                  fecha_desde: ${text.substring(week_start, 0, 10)}
                  fecha_hasta: ${week_end}
          result: expenses_response
        retry:
          predicate: ${default_retry_predicate}
          max_retries: 3
          backoff:
            initial_delay: 5
            max_delay: 60
            multiplier: 2

    - generate_summary:
        try:
          call: http.post
          args:
            url: ${base_url + "/api/v1/calc"}
            headers:
              Content-Type: "application/json"
            body:
              request_id: ${"wf2-calc-" + week_start}
              timestamp: ${today}
              payload:
                operacion: "resumen_periodo"
                params:
                  ventas: ${sales_response.body.data.registros}
                  gastos: ${expenses_response.body.data.registros}
                  periodo: ${week_start + " a " + week_end}
          result: summary_response
        retry:
          predicate: ${default_retry_predicate}
          max_retries: 2
          backoff:
            initial_delay: 2
            max_delay: 15
            multiplier: 2

    - store_report:
        try:
          call: http.post
          args:
            url: ${base_url + "/api/v1/sheets/write"}
            headers:
              Content-Type: "application/json"
            body:
              request_id: ${"wf2-store-" + week_start}
              timestamp: ${today}
              payload:
                hoja: "Gastos"
                registro:
                  fecha: ${week_end}
                  categoria: "reporte_semanal"
                  descripcion: ${"Resumen " + week_start + " a " + week_end}
                  monto: 0
                idempotency_key: ${"wf2-report-" + week_start}
          result: store_response
        retry:
          predicate: ${default_retry_predicate}
          max_retries: 2
          backoff:
            initial_delay: 2
            max_delay: 15
            multiplier: 2

    - return_result:
        return:
          status: "completed"
          periodo: ${week_start + " a " + week_end}
          resumen: ${summary_response.body.data}

default_retry_predicate:
  params: [e]
  steps:
    - check:
        switch:
          - condition: ${e.code == 429 or e.code == 502 or e.code == 503}
            return: true
        next: no
    - no:
        return: false
```

### Configuración del Cloud Scheduler

```bash
gcloud scheduler jobs create http weekly-summary-trigger \
  --schedule="0 9 * * 1" \
  --time-zone="America/Mexico_City" \
  --uri="https://workflowexecutions.googleapis.com/v1/projects/PROJECT_ID/locations/us-central1/workflows/weekly-summary/executions" \
  --http-method=POST \
  --oauth-service-account-email="workflow-invoker@PROJECT_ID.iam.gserviceaccount.com"
```

---

## 8.4 Workflow 3: `low_margin_alert`

### Propósito
Subworkflow invocado por WF1 cuando detecta que algún sabor tiene margen bruto inferior al 40%. Genera un mensaje de alerta estructurado.

### Diagrama

```
┌──────────────────────────────┐
│  WF1: post_write_check       │
│  (margen < 40% detectado)    │
└──────────────┬───────────────┘
               │ subworkflow call
               ▼
┌──────────────────────────────────────────────────────────────────┐
│  SUBWORKFLOW: low_margin_alert                                   │
│                                                                  │
│  ┌────────────────────────────────┐                              │
│  │ PASO 1: identify_low_margins   │                              │
│  │ Filtra sabores con margen      │                              │
│  │ < umbral (40%)                 │                              │
│  └──────────────┬─────────────────┘                              │
│                 │                                                 │
│                 ▼                                                 │
│  ┌────────────────────────────────┐                              │
│  │ PASO 2: build_alert_message    │                              │
│  │ Construye mensaje de alerta    │                              │
│  │ con sabores afectados,         │                              │
│  │ margen actual y recomendación  │                              │
│  └──────────────┬─────────────────┘                              │
│                 │                                                 │
│                 ▼                                                 │
│  ┌────────────────────────────────┐                              │
│  │ PASO 3: log_alert              │                              │
│  │ Registra la alerta en          │                              │
│  │ Cloud Logging con severity     │                              │
│  │ WARNING                        │                              │
│  └────────────────────────────────┘                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Definición en Google Workflows (YAML)

```yaml
main:
  params: [input]
  steps:
    - identify_low_margins:
        assign:
          - alertas: []
          - margenes: ${input.margenes}
          - umbral: ${input.umbral}

    - filter_low:
        for:
          value: sabor_data
          in: ${margenes}
          steps:
            - check_margin:
                switch:
                  - condition: ${sabor_data.margen_porcentaje < umbral}
                    steps:
                      - add_alert:
                          assign:
                            - alertas: ${list.concat(alertas, sabor_data)}

    - check_any_alerts:
        switch:
          - condition: ${len(alertas) == 0}
            return:
              status: "no_alerts"
              message: "Todos los sabores están sobre el umbral."
        next: build_message

    - build_message:
        assign:
          - alert_message:
              tipo: "LOW_MARGIN_WARNING"
              severidad: "WARNING"
              mes: ${input.mes}
              umbral_pct: ${umbral}
              sabores_afectados: ${alertas}
              recomendacion: "Revisar costos de producción o ajustar precios de los sabores con margen inferior al umbral."
              timestamp: ${time.format(sys.now())}

    - log_alert:
        call: sys.log
        args:
          json: ${alert_message}
          severity: "WARNING"

    - return_alert:
        return: ${alert_message}
```

---

## 8.5 Manejo de Errores

### Estrategia por tipo de error

| Tipo de error | Código HTTP | Estrategia | Ejemplo |
|---|---|---|---|
| **Transitorio** (red, timeout) | 429, 502, 503 | Reintento automático con backoff exponencial | Sheets API temporalmente no disponible |
| **Permanente** (datos inválidos) | 400, 404 | Fallo inmediato, sin reintento | Hoja no encontrada, campo inválido |
| **Autenticación** | 401, 403 | Fallo inmediato, log con severity ERROR | Service account expirado |
| **Error interno del tool** | 500 | Reintento limitado (1 vez), luego fallo | Error no anticipado en Cloud Function |

### Manejo en los pasos del workflow

Cada paso que llama a un tool está envuelto en un bloque `try` con política de reintento. Si todos los reintentos fallan, el workflow entra en estado `FAILED` y Cloud Logging registra el error completo.

```yaml
# Patrón estándar de error handling en cada paso
- step_name:
    try:
      call: http.post
      args:
        url: ${tool_url}
        body: ${payload}
      result: response
    retry:
      predicate: ${default_retry_predicate}  # Solo reintenta 429, 502, 503
      max_retries: 3
      backoff:
        initial_delay: 2    # Espera 2s antes del 1er reintento
        max_delay: 30        # Máximo 30s entre reintentos
        multiplier: 2        # Duplica el delay en cada reintento
    except:
      as: error
      steps:
        - log_failure:
            call: sys.log
            args:
              json:
                workflow: "post_write_check"
                step: "step_name"
                error_code: ${error.code}
                error_message: ${error.message}
                timestamp: ${time.format(sys.now())}
              severity: "ERROR"
        - raise_error:
            raise: ${error}
```

---

## 8.6 Política de Reintentos

| Parámetro | WF1 (post_write_check) | WF2 (weekly_summary) | WF3 (low_margin_alert) |
|---|---|---|---|
| **Max reintentos** | 3 | 3 | 0 (subworkflow, no reintenta) |
| **Delay inicial** | 2 segundos | 5 segundos | N/A |
| **Delay máximo** | 30 segundos | 60 segundos | N/A |
| **Multiplicador** | 2x (exponencial) | 2x (exponencial) | N/A |
| **Errores reintentables** | 429, 502, 503 | 429, 502, 503 | N/A |
| **Errores fatales** | 400, 401, 403, 404, 500 | 400, 401, 403, 404, 500 | Cualquiera |

### Ejemplo de secuencia de reintentos (WF1)

```
Intento 1: t=0s     → Sheets API responde 502
Intento 2: t=2s     → Sheets API responde 502  
Intento 3: t=6s     → Sheets API responde 200 ✓ (éxito)

Intento 1: t=0s     → Sheets API responde 502
Intento 2: t=2s     → Sheets API responde 502
Intento 3: t=6s     → Sheets API responde 502
Intento 4: NO       → max_retries alcanzado → FAILED
```

---

## 8.7 Integración desde el Agente

### ¿Cómo el orchestrator dispara un workflow?

El orchestrator invoca Google Workflows vía la API REST de forma **asíncrona** (fire-and-forget para WF1) o **síncrona** (espera resultado para WF2 cuando se consulta bajo demanda).

```
┌────────────────────┐
│   ORCHESTRATOR      │
│   (Cloud Run)       │
└──────┬─────────────┘
       │
       ├── Tras sheets_writer exitoso ──► WF1 (async, no bloquea la respuesta al usuario)
       │
       └── Usuario pregunta "¿cómo fue mi semana?" ──► Lee último resultado de WF2 desde Sheets
```

### Código de integración (Python / FastAPI)

```python
from google.cloud import workflows_v1
from google.cloud.workflows import executions_v1

async def trigger_post_write_check(registro: dict):
    """Dispara WF1 de forma asíncrona tras un registro exitoso."""
    client = executions_v1.ExecutionsAsyncClient()

    execution = executions_v1.Execution(
        argument=json.dumps({
            "registro": registro,
            "timestamp": datetime.utcnow().isoformat()
        })
    )

    parent = (
        "projects/brewfinance-prod"
        "/locations/us-central1"
        "/workflows/post-write-check"
    )

    # Fire-and-forget: no espera resultado
    await client.create_execution(
        parent=parent,
        execution=execution
    )
```

### Flujo completo con workflow integrado

```
1. Usuario: "Registra 10 de fresa a $45 en el gimnasio"
2. Orchestrator → LLM (Gemini): parsea intención → ACTION: sheets_writer
3. Orchestrator → Guardrail: valida parámetros ✓
4. Orchestrator → sheets_writer (Cloud Function): inserta fila ✓
5. Orchestrator → WF1 post_write_check (async): dispara verificación en background
6. Orchestrator → LLM (Gemini): genera respuesta con confirmación
7. Usuario recibe: "Listo, registré 10 de fresa 345ml a $45 en gimnasio."
   ─── mientras tanto, en background: ───
8. WF1 → sheets_reader: lee ventas del mes
9. WF1 → sheets_reader: lee costos
10. WF1 → calculator: calcula márgenes actualizados
11. WF1 → evalúa: ¿margen < 40%?
    - SÍ → WF3 low_margin_alert → log WARNING
    - NO → fin silencioso
```

El usuario no espera por el workflow — la respuesta al registro llega en ~2-3 segundos. El workflow corre en background y solo genera una alerta si detecta un problema.
