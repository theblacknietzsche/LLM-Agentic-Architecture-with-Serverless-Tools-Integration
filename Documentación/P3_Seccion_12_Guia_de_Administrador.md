# PROYECTO 3 – Sección 12: Guía de Administrador

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco  
**Documento:** Guía de Administrador — BrewFinance Agent v1.0.0

---

## 1. Requisitos Previos

### 1.1 Software local

| Software | Versión mínima | Propósito | Instalación |
|---|---|---|---|
| Python | 3.12+ | Runtime del proyecto | `https://python.org/downloads` |
| Docker | 24.0+ | Contenedores de desarrollo | `https://docs.docker.com/get-docker` |
| Docker Compose | 2.20+ | Orquestación local | Incluido con Docker Desktop |
| Google Cloud SDK | 480+ | Deploy y gestión de GCP | `https://cloud.google.com/sdk/docs/install` |
| Git | 2.40+ | Control de versiones | `https://git-scm.com/downloads` |
| Trivy | 0.50+ | Vulnerability scanning | `https://aquasecurity.github.io/trivy` |

### 1.2 Cuentas y accesos

| Recurso | Qué se necesita |
|---|---|
| Google Cloud Platform | Proyecto GCP con billing habilitado |
| Vertex AI API | API habilitada en el proyecto GCP |
| Google Sheets API | API habilitada en el proyecto GCP |
| Repositorio Git | Acceso al repositorio `brewfinance-agent` |

---

## 2. Configuración del Entorno Local (Desarrollo)

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/theblacknietzsche/LLM-Agentic-Architecture-with-Serverless-Tools-Integration/tree/main
cd brewfinance-agent
```

### Paso 2: Crear el archivo de variables de entorno

```bash
cp .env.example .env
```

### Paso 3: Obtener la API Key de Gemini

1. Ir a Google AI Studio: `https://aistudio.google.com/apikey`
2. Crear una nueva API Key
3. Copiar la key y pegarla en el archivo `.env`:

```env
GOOGLE_API_KEY=AIzaSy...tu_key_aqui
```

### Paso 4: Configurar Google Sheets

1. Crear un Service Account en GCP Console → IAM & Admin → Service Accounts
2. Asignarle el rol `Editor` de la spreadsheet específica
3. Descargar el JSON de credenciales
4. Configurar en `.env`:

```env
SHEETS_SPREADSHEET_ID=1AbC...tu_spreadsheet_id
SHEETS_SERVICE_ACCOUNT_PATH=./secrets/service_account.json
```

### Paso 5: Levantar el sistema con Docker Compose

```bash
docker compose up --build
```

Esto levanta 3 servicios:

| Servicio | Puerto | URL |
|---|---|---|
| Orchestrator | 8000 | `http://localhost:8000` |
| Mock Sheets API | 8001 | `http://localhost:8001` |
| Logging Service | 8002 | `http://localhost:8002` |

### Paso 6: Verificar que todo funciona

```bash
# Health check del orchestrator
curl http://localhost:8000/health

# Respuesta esperada:
# {"status":"ok","service":"brewfinance-orchestrator","version":"1.0.0",...}

# Health check del mock API
curl http://localhost:8001/health

# Health check del logging
curl http://localhost:8002/health
```

### Paso 7: Probar una consulta

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{"message": "¿Cuántos sabores tengo?"}'
```

---

## 3. Estructura del Google Sheets (Producción)

Cuando conectes con Google Sheets real, el spreadsheet debe tener 3 hojas con esta estructura exacta:

### Hoja: Ventas

| Columna A | Columna B | Columna C | Columna D | Columna E | Columna F |
|---|---|---|---|---|---|
| **fecha** | **sabor** | **presentacion** | **cantidad** | **precio_unitario** | **canal** |
| 2026-06-01 | mango | 345ml | 5 | 45.00 | gimnasio |

### Hoja: Costos

| Columna A | Columna B | Columna C | Columna D | Columna E | Columna F |
|---|---|---|---|---|---|
| **sabor** | **presentacion** | **costo_ingredientes** | **costo_envase** | **costo_mano_obra** | **costo_unitario_total** |
| mango | 345ml | 10.00 | 4.50 | 3.00 | 17.50 |

### Hoja: Gastos

| Columna A | Columna B | Columna C | Columna D |
|---|---|---|---|
| **fecha** | **categoria** | **descripcion** | **monto** |
| 2026-06-01 | envases | Botellas 345ml x100 | 450.00 |

**Los encabezados de la fila 1 deben ser exactamente como se muestran (minúsculas, sin tildes).** El agente usa estos nombres para leer y escribir datos.

---

## 4. Ejecución de Tests

### Tests unitarios (sin dependencias externas)

```bash
# Instalar dependencias de test
pip install -r requirements.txt -r requirements-mock.txt -r requirements-test.txt

# Correr tests unitarios
pytest tests/unit/ -v
```

Resultado esperado:

```
tests/unit/test_guardrails.py::TestSheetsReaderGuardrails::test_valid_read_ventas PASSED
tests/unit/test_guardrails.py::TestSheetsReaderGuardrails::test_reject_invalid_sheet PASSED
tests/unit/test_guardrails.py::TestSheetsWriterGuardrails::test_valid_sale_registration PASSED
tests/unit/test_guardrails.py::TestSheetsWriterGuardrails::test_reject_negative_quantity PASSED
tests/unit/test_guardrails.py::TestSheetsWriterGuardrails::test_reject_unknown_sabor PASSED
...
tests/unit/test_calculator_ops.py::TestMargenPorSabor::test_basic_margin PASSED
tests/unit/test_calculator_ops.py::TestPuntoEquilibrio::test_basic_breakeven PASSED
...
```

### Tests de integración (requiere Mock API)

```bash
# Opción A: Con Docker
docker compose up mock-sheets-api -d
pytest tests/integration/ -v

# Opción B: Sin Docker (usando TestClient de FastAPI)
pytest tests/integration/ -v
```

### Todos los tests

```bash
pytest tests/ -v
```

---

## 5. Vulnerability Scanning

### Escanear imágenes Docker

```bash
# Construir las imágenes
docker compose build

# Escanear cada imagen
trivy image brewfinance-orchestrator:latest
trivy image brewfinance-mock-sheets:latest
trivy image brewfinance-logging:latest

# Solo vulnerabilidades HIGH y CRITICAL
trivy image --severity HIGH,CRITICAL brewfinance-orchestrator:latest
```

### Criterio de aceptación

- **CRITICAL:** No se permite ninguna. Corregir antes de desplegar.
- **HIGH:** Evaluar caso por caso. Documentar excepciones.
- **MEDIUM/LOW:** Informativos, no bloquean deploy.

---

## 6. Deploy a Producción (Google Cloud Platform)

### 6.1 Configuración inicial del proyecto GCP

```bash
# Autenticarse
gcloud auth login

# Crear proyecto (o seleccionar existente)
gcloud projects create brewfinance-prod --name="BrewFinance Agent"
gcloud config set project brewfinance-prod

# Habilitar APIs necesarias
gcloud services enable \
  aiplatform.googleapis.com \
  cloudfunctions.googleapis.com \
  run.googleapis.com \
  workflows.googleapis.com \
  sheets.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  logging.googleapis.com \
  cloudtrace.googleapis.com \
  monitoring.googleapis.com
```

### 6.2 Crear Service Accounts

```bash
# Service account para Cloud Functions (tools)
gcloud iam service-accounts create bf-functions \
  --display-name="BrewFinance Cloud Functions"

# Service account para Cloud Run (orchestrator)
gcloud iam service-accounts create bf-orchestrator \
  --display-name="BrewFinance Orchestrator"

# Service account para Workflows
gcloud iam service-accounts create bf-workflows \
  --display-name="BrewFinance Workflows"
```

### 6.3 Asignar permisos (Least Privilege)

```bash
PROJECT_ID=$(gcloud config get-value project)

# Cloud Functions: acceso a Sheets + Secrets
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:bf-functions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Orchestrator: invocar functions + usar Vertex AI + invocar workflows + acceder a secrets
for role in roles/cloudfunctions.invoker roles/aiplatform.user roles/secretmanager.secretAccessor roles/workflows.invoker; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:bf-orchestrator@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$role"
done

# Workflows: invocar functions + escribir logs
for role in roles/cloudfunctions.invoker roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:bf-workflows@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$role"
done
```

### 6.4 Almacenar Secrets

```bash
# API Key de Gemini
echo -n "AIzaSy...tu_key" | gcloud secrets create brewfinance-gemini-key \
  --data-file=- --replication-policy="automatic"

# ID del Spreadsheet
echo -n "1AbC...tu_id" | gcloud secrets create brewfinance-sheet-id \
  --data-file=- --replication-policy="automatic"
```

### 6.5 Crear Artifact Registry

```bash
gcloud artifacts repositories create brewfinance \
  --repository-format=docker \
  --location=us-central1 \
  --description="BrewFinance Docker images"
```

### 6.6 Deploy de Cloud Functions (4 tools)

```bash
REGION=us-central1
SA=bf-functions@$PROJECT_ID.iam.gserviceaccount.com

# Sheets Reader
gcloud functions deploy bf-sheets-reader \
  --gen2 --runtime=python312 --region=$REGION \
  --source=./cloud_functions/sheets_reader \
  --entry-point=main --trigger-http \
  --no-allow-unauthenticated \
  --service-account=$SA \
  --set-secrets="SHEETS_SPREADSHEET_ID=brewfinance-sheet-id:latest" \
  --memory=256Mi --timeout=30s --max-instances=5

# Sheets Writer
gcloud functions deploy bf-sheets-writer \
  --gen2 --runtime=python312 --region=$REGION \
  --source=./cloud_functions/sheets_writer \
  --entry-point=main --trigger-http \
  --no-allow-unauthenticated \
  --service-account=$SA \
  --set-secrets="SHEETS_SPREADSHEET_ID=brewfinance-sheet-id:latest" \
  --memory=256Mi --timeout=30s --max-instances=5

# Calculator
gcloud functions deploy bf-calculator \
  --gen2 --runtime=python312 --region=$REGION \
  --source=./cloud_functions/calculator \
  --entry-point=main --trigger-http \
  --no-allow-unauthenticated \
  --service-account=$SA \
  --memory=256Mi --timeout=30s --max-instances=5

# Report Generator
gcloud functions deploy bf-report-generator \
  --gen2 --runtime=python312 --region=$REGION \
  --source=./cloud_functions/report_generator \
  --entry-point=main --trigger-http \
  --no-allow-unauthenticated \
  --service-account=$SA \
  --memory=256Mi --timeout=30s --max-instances=5
```

### 6.7 Build y Deploy del Orchestrator (Cloud Run)

```bash
# Build de la imagen
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/brewfinance/orchestrator:v1.0.0 \
  -f docker/Dockerfile.orchestrator .

# Push a Artifact Registry
docker push us-central1-docker.pkg.dev/$PROJECT_ID/brewfinance/orchestrator:v1.0.0

# Obtener URL base de las Cloud Functions
TOOLS_URL="https://$REGION-$PROJECT_ID.cloudfunctions.net"

# Deploy a Cloud Run
gcloud run deploy brewfinance-orchestrator \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/brewfinance/orchestrator:v1.0.0 \
  --region=$REGION --platform=managed \
  --no-allow-unauthenticated \
  --service-account=bf-orchestrator@$PROJECT_ID.iam.gserviceaccount.com \
  --set-secrets="GOOGLE_API_KEY=brewfinance-gemini-key:latest" \
  --set-env-vars="ENVIRONMENT=production,TOOLS_BASE_URL=$TOOLS_URL,MAX_REACT_STEPS=5,DEFAULT_MODEL=gemini-2.5-flash,FALLBACK_MODEL=gemini-2.5-pro" \
  --memory=512Mi --cpu=1 \
  --min-instances=0 --max-instances=3 \
  --timeout=60s
```

### 6.8 Deploy de Google Workflows

```bash
WF_SA=bf-workflows@$PROJECT_ID.iam.gserviceaccount.com

gcloud workflows deploy post-write-check \
  --location=$REGION \
  --source=./workflows/post_write_check.yaml \
  --service-account=$WF_SA

gcloud workflows deploy weekly-summary \
  --location=$REGION \
  --source=./workflows/weekly_summary.yaml \
  --service-account=$WF_SA

gcloud workflows deploy low-margin-alert \
  --location=$REGION \
  --source=./workflows/low_margin_alert.yaml \
  --service-account=$WF_SA
```

### 6.9 Configurar Cloud Scheduler (resumen semanal)

```bash
# Obtener URL del orchestrator
ORCH_URL=$(gcloud run services describe brewfinance-orchestrator \
  --region=$REGION --format='value(status.url)')

gcloud scheduler jobs create http weekly-summary-trigger \
  --schedule="0 9 * * 1" \
  --time-zone="America/Mexico_City" \
  --uri="https://workflowexecutions.googleapis.com/v1/projects/$PROJECT_ID/locations/$REGION/workflows/weekly-summary/executions" \
  --http-method=POST \
  --oauth-service-account-email=$WF_SA
```

### 6.10 Verificar el deploy

```bash
# Obtener URL
ORCH_URL=$(gcloud run services describe brewfinance-orchestrator \
  --region=$REGION --format='value(status.url)')

# Health check
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" "$ORCH_URL/health"

# Prueba funcional
curl -X POST "$ORCH_URL/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tu-api-key-produccion" \
  -d '{"message": "¿Cuántos sabores tengo?"}'
```

---

## 7. Monitoreo y Observabilidad

### 7.1 Ver logs del agente

```bash
# Logs del orchestrator (Cloud Run)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=brewfinance-orchestrator" \
  --limit=20 --format=json

# Logs de una Cloud Function específica
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=bf-sheets-reader" \
  --limit=20 --format=json

# Logs de errores (todos los componentes)
gcloud logging read "severity>=ERROR" --limit=50 --format=json
```

### 7.2 Ver logs en la consola web

1. Ir a `https://console.cloud.google.com/logs`
2. Filtrar por `resource.type="cloud_run_revision"`
3. Buscar por `request_id` para rastrear una consulta completa

### 7.3 Ver traces de latencia

1. Ir a `https://console.cloud.google.com/traces`
2. Filtrar por el servicio `brewfinance-orchestrator`
3. Click en un trace para ver el desglose de latencia por componente

### 7.4 Crear alertas

```bash
# Alerta: tasa de errores > 10% en 5 minutos
gcloud monitoring policies create --policy-from-file=- << 'EOF'
displayName: "BrewFinance - Error Rate Alta"
conditions:
  - displayName: "Error rate > 10%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class!="2xx"'
      comparison: COMPARISON_GT
      thresholdValue: 0.1
      duration: 300s
EOF
```

---

## 8. Mantenimiento

### 8.1 Agregar un nuevo sabor

1. Agregar el sabor en Google Sheets → Hoja Costos (nueva fila con costos de producción)
2. Actualizar `src/models/errors.py` → `VALID_SABORES` (agregar el nuevo sabor)
3. Actualizar `mock_api/storage.py` → `COSTOS` (agregar datos de prueba)
4. Correr tests: `pytest tests/ -v`
5. Redesplegar: `gcloud builds submit --config=cloudbuild-cd.yaml`

### 8.2 Agregar un nuevo canal de venta

1. Actualizar `src/models/errors.py` → `VALID_CANALES`
2. Actualizar `config/tools_schema.json` → enum de `canal` en sheets_writer
3. Correr tests y redesplegar

### 8.3 Actualizar el modelo de Gemini

1. Editar `.env` o las variables de entorno en Cloud Run:
   - `DEFAULT_MODEL=gemini-2.5-flash` → nuevo modelo
   - `FALLBACK_MODEL=gemini-2.5-pro` → nuevo modelo
2. Redesplegar el orchestrator

### 8.4 Rotar API Keys

```bash
# Crear nueva versión del secret
echo -n "nueva_key" | gcloud secrets versions add brewfinance-gemini-key --data-file=-

# El Cloud Run usa la versión `:latest`, así que tomará la nueva automáticamente
# Forzar nuevo deploy para aplicar inmediatamente:
gcloud run services update brewfinance-orchestrator --region=us-central1
```

### 8.5 Revisar costos

```bash
# Ver billing del proyecto
gcloud billing budgets list

# Ver invocaciones de Cloud Functions del último mes
gcloud logging read "resource.type=cloud_function" --freshness=30d --format="json" | jq length
```

---

## 9. Troubleshooting

| Problema | Causa probable | Solución |
|---|---|---|
| `docker compose up` falla con "port already in use" | Otro servicio usando el puerto 8000, 8001 o 8002 | Detener el servicio conflictivo o cambiar puertos en `docker-compose.yml` |
| "GOOGLE_API_KEY no configurada" al iniciar | Falta el archivo `.env` o la variable está vacía | Verificar que `.env` existe y tiene la key |
| Agente responde "No se puede conectar con sheets_reader" | Mock API no está corriendo | Verificar `docker compose ps` — el mock-sheets-api debe estar healthy |
| Error 401 en Cloud Run | Token de autenticación expirado o API Key incorrecta | Regenerar token: `gcloud auth print-identity-token` |
| Cloud Function timeout | La operación toma más de 30s | Verificar que Google Sheets no esté saturado. Aumentar timeout si es necesario |
| Tests fallan con "ModuleNotFoundError" | Dependencias no instaladas | Ejecutar `pip install -r requirements.txt -r requirements-mock.txt -r requirements-test.txt` |
| "quota exceeded" en Sheets API | Más de 300 requests/minuto a la API | Reducir frecuencia de consultas. Implementar cache si es recurrente |
| Workflow en estado FAILED | Un tool no respondió o retornó error | Revisar logs del workflow: `gcloud logging read "resource.type=workflows.googleapis.com"` |
| Imagen Docker muy grande (>500MB) | Build sin multi-stage o sin slim | Verificar que el Dockerfile use `python:3.12-slim` y multi-stage |
| Trivy reporta vulnerabilidad CRITICAL | Dependencia con CVE conocido | Actualizar la dependencia en `requirements.txt` y rebuild |

---

## 10. Arquitectura de Referencia Rápida

```
USUARIO
  │
  ▼
API Gateway (Cloud Function) ─── auth + rate limit
  │
  ▼
Orchestrator (Cloud Run) ─── FastAPI + ReAct loop
  │
  ├──► Gemini 2.5 Flash / Pro (Vertex AI)
  │
  ├──► bf-sheets-reader (Cloud Function) ──► Google Sheets
  ├──► bf-sheets-writer (Cloud Function) ──► Google Sheets
  ├──► bf-calculator (Cloud Function)
  ├──► bf-report-generator (Cloud Function)
  │
  ├──► Google Workflows (post_write_check, weekly_summary)
  │
  └──► Cloud Logging + Cloud Trace + Cloud Monitoring
```
