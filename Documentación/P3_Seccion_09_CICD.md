# PROYECTO 3 – Sección 9: CI/CD Completo

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 9.1 Estrategia de CI/CD

El pipeline de CI/CD utiliza **Google Cloud Build** como motor de ejecución, conectado a un repositorio **GitHub** como fuente de código. Se definen dos pipelines principales: uno para integración continua (CI) que corre en cada push/PR, y otro para despliegue continuo (CD) que se ejecuta al hacer merge a la rama `main`.

| Pipeline | Trigger | Propósito |
|---|---|---|
| **CI** (`ci.yaml`) | Push a cualquier rama / Pull Request | Tests, linting, build de imágenes, vulnerability scanning |
| **CD** (`cd.yaml`) | Merge a `main` | Deploy de Cloud Functions, Cloud Run y Workflows a producción |

### Flujo general

```
┌──────────┐     ┌──────────────────────────────────────────────────────────┐
│  GitHub   │     │                CLOUD BUILD                              │
│           │     │                                                          │
│  push /   │────►│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐  │
│  PR       │     │  │  Lint   │─►│  Test   │─►│  Build  │─►│  Scan    │  │
│           │     │  │         │  │         │  │ Docker  │  │  Trivy   │  │
│           │     │  └─────────┘  └─────────┘  └─────────┘  └──────────┘  │
│           │     │                                              CI ▲       │
│           │     │──────────────────────────────────────────────────────── │
│  merge    │────►│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  a main   │     │  │  Deploy  │─►│  Deploy  │─►│  Deploy  │             │
│           │     │  │  Cloud   │  │  Cloud   │  │  Google  │             │
│           │     │  │Functions │  │   Run    │  │Workflows │             │
│           │     │  └──────────┘  └──────────┘  └──────────┘  CD ▲       │
└──────────┘     └──────────────────────────────────────────────────────── ┘
```

---

## 9.2 Pipeline de CI (`ci.yaml`)

```yaml
# cloudbuild-ci.yaml
steps:

  # ─── PASO 1: Lint ───
  - id: "lint"
    name: "python:3.12-slim"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        pip install --no-cache-dir ruff
        echo "=== Linting orchestrator ==="
        ruff check src/
        echo "=== Linting mock API ==="
        ruff check mock_api/
        echo "=== Linting logging service ==="
        ruff check logging_service/

  # ─── PASO 2: Tests unitarios ───
  - id: "unit-tests"
    name: "python:3.12-slim"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        pip install --no-cache-dir -r requirements.txt -r requirements-mock.txt -r requirements-test.txt
        echo "=== Running unit tests ==="
        pytest tests/unit/ -v --tb=short --junitxml=test-results/unit.xml
    waitFor: ["lint"]

  # ─── PASO 3: Tests de integración (con mock API) ───
  - id: "integration-tests"
    name: "python:3.12-slim"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        pip install --no-cache-dir -r requirements.txt -r requirements-mock.txt -r requirements-test.txt
        echo "=== Running integration tests ==="
        pytest tests/integration/ -v --tb=short --junitxml=test-results/integration.xml
    waitFor: ["unit-tests"]

  # ─── PASO 4: Build imagen del orchestrator ───
  - id: "build-orchestrator"
    name: "gcr.io/cloud-builders/docker"
    args:
      - "build"
      - "-t"
      - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/orchestrator:${SHORT_SHA}"
      - "-t"
      - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/orchestrator:latest"
      - "-f"
      - "docker/Dockerfile.orchestrator"
      - "."
    waitFor: ["integration-tests"]

  # ─── PASO 5: Build imagen del mock API ───
  - id: "build-mock-api"
    name: "gcr.io/cloud-builders/docker"
    args:
      - "build"
      - "-t"
      - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/mock-sheets-api:${SHORT_SHA}"
      - "-f"
      - "docker/Dockerfile.mock-api"
      - "."
    waitFor: ["integration-tests"]

  # ─── PASO 6: Build imagen del logging service ───
  - id: "build-logging"
    name: "gcr.io/cloud-builders/docker"
    args:
      - "build"
      - "-t"
      - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/logging-service:${SHORT_SHA}"
      - "-f"
      - "docker/Dockerfile.logging"
      - "."
    waitFor: ["integration-tests"]

  # ─── PASO 7: Vulnerability scanning (Trivy) ───
  - id: "scan-orchestrator"
    name: "aquasec/trivy:latest"
    args:
      - "image"
      - "--exit-code"
      - "1"
      - "--severity"
      - "CRITICAL"
      - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/orchestrator:${SHORT_SHA}"
    waitFor: ["build-orchestrator"]

  - id: "scan-mock-api"
    name: "aquasec/trivy:latest"
    args:
      - "image"
      - "--exit-code"
      - "1"
      - "--severity"
      - "CRITICAL"
      - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/mock-sheets-api:${SHORT_SHA}"
    waitFor: ["build-mock-api"]

  - id: "scan-logging"
    name: "aquasec/trivy:latest"
    args:
      - "image"
      - "--exit-code"
      - "1"
      - "--severity"
      - "CRITICAL"
      - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/logging-service:${SHORT_SHA}"
    waitFor: ["build-logging"]

  # ─── PASO 8: Push imágenes a Artifact Registry ───
  - id: "push-images"
    name: "gcr.io/cloud-builders/docker"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        docker push ${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/orchestrator:${SHORT_SHA}
        docker push ${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/orchestrator:latest
        docker push ${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/mock-sheets-api:${SHORT_SHA}
        docker push ${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/logging-service:${SHORT_SHA}
    waitFor: ["scan-orchestrator", "scan-mock-api", "scan-logging"]

substitutions:
  _REGION: "us-central1"
  _REPO: "brewfinance"

options:
  logging: CLOUD_LOGGING_ONLY
```

---

## 9.3 Pipeline de CD (`cd.yaml`)

```yaml
# cloudbuild-cd.yaml
steps:

  # ─── PASO 1: Deploy Cloud Functions (4 tools) ───
  - id: "deploy-sheets-reader"
    name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "gcloud"
    args:
      - "functions"
      - "deploy"
      - "bf-sheets-reader"
      - "--gen2"
      - "--runtime=python312"
      - "--region=${_REGION}"
      - "--source=./cloud_functions/sheets_reader"
      - "--entry-point=main"
      - "--trigger-http"
      - "--no-allow-unauthenticated"
      - "--service-account=${_FUNCTIONS_SA}"
      - "--set-secrets=SHEETS_SPREADSHEET_ID=brewfinance-sheet-id:latest"
      - "--memory=256Mi"
      - "--timeout=30s"
      - "--max-instances=5"

  - id: "deploy-sheets-writer"
    name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "gcloud"
    args:
      - "functions"
      - "deploy"
      - "bf-sheets-writer"
      - "--gen2"
      - "--runtime=python312"
      - "--region=${_REGION}"
      - "--source=./cloud_functions/sheets_writer"
      - "--entry-point=main"
      - "--trigger-http"
      - "--no-allow-unauthenticated"
      - "--service-account=${_FUNCTIONS_SA}"
      - "--set-secrets=SHEETS_SPREADSHEET_ID=brewfinance-sheet-id:latest"
      - "--memory=256Mi"
      - "--timeout=30s"
      - "--max-instances=5"
    waitFor: ["-"]

  - id: "deploy-calculator"
    name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "gcloud"
    args:
      - "functions"
      - "deploy"
      - "bf-calculator"
      - "--gen2"
      - "--runtime=python312"
      - "--region=${_REGION}"
      - "--source=./cloud_functions/calculator"
      - "--entry-point=main"
      - "--trigger-http"
      - "--no-allow-unauthenticated"
      - "--service-account=${_FUNCTIONS_SA}"
      - "--memory=256Mi"
      - "--timeout=30s"
      - "--max-instances=5"
    waitFor: ["-"]

  - id: "deploy-report-generator"
    name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "gcloud"
    args:
      - "functions"
      - "deploy"
      - "bf-report-generator"
      - "--gen2"
      - "--runtime=python312"
      - "--region=${_REGION}"
      - "--source=./cloud_functions/report_generator"
      - "--entry-point=main"
      - "--trigger-http"
      - "--no-allow-unauthenticated"
      - "--service-account=${_FUNCTIONS_SA}"
      - "--memory=256Mi"
      - "--timeout=30s"
      - "--max-instances=5"
    waitFor: ["-"]

  # ─── PASO 2: Deploy Orchestrator (Cloud Run) ───
  - id: "deploy-orchestrator"
    name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "gcloud"
    args:
      - "run"
      - "deploy"
      - "brewfinance-orchestrator"
      - "--image=${_REGION}-docker.pkg.dev/${PROJECT_ID}/${_REPO}/orchestrator:${SHORT_SHA}"
      - "--region=${_REGION}"
      - "--platform=managed"
      - "--no-allow-unauthenticated"
      - "--service-account=${_ORCHESTRATOR_SA}"
      - "--set-secrets=GOOGLE_API_KEY=brewfinance-gemini-key:latest"
      - "--set-env-vars=ENVIRONMENT=production,TOOLS_BASE_URL=${_TOOLS_BASE_URL}"
      - "--memory=512Mi"
      - "--cpu=1"
      - "--min-instances=0"
      - "--max-instances=3"
      - "--timeout=60s"
    waitFor:
      - "deploy-sheets-reader"
      - "deploy-sheets-writer"
      - "deploy-calculator"
      - "deploy-report-generator"

  # ─── PASO 3: Deploy Google Workflows ───
  - id: "deploy-workflow-post-write"
    name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "gcloud"
    args:
      - "workflows"
      - "deploy"
      - "post-write-check"
      - "--location=${_REGION}"
      - "--source=./workflows/post_write_check.yaml"
      - "--service-account=${_WORKFLOW_SA}"
      - "--set-env-vars=TOOLS_BASE_URL=${_TOOLS_BASE_URL}"
    waitFor: ["deploy-orchestrator"]

  - id: "deploy-workflow-weekly-summary"
    name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "gcloud"
    args:
      - "workflows"
      - "deploy"
      - "weekly-summary"
      - "--location=${_REGION}"
      - "--source=./workflows/weekly_summary.yaml"
      - "--service-account=${_WORKFLOW_SA}"
      - "--set-env-vars=TOOLS_BASE_URL=${_TOOLS_BASE_URL}"
    waitFor: ["deploy-orchestrator"]

  - id: "deploy-workflow-low-margin"
    name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "gcloud"
    args:
      - "workflows"
      - "deploy"
      - "low-margin-alert"
      - "--location=${_REGION}"
      - "--source=./workflows/low_margin_alert.yaml"
      - "--service-account=${_WORKFLOW_SA}"
    waitFor: ["deploy-orchestrator"]

  # ─── PASO 4: Smoke test post-deploy ───
  - id: "smoke-test"
    name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        echo "=== Smoke test: health check ==="
        ORCHESTRATOR_URL=$(gcloud run services describe brewfinance-orchestrator \
          --region=${_REGION} --format='value(status.url)')

        TOKEN=$(gcloud auth print-identity-token)

        STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
          -H "Authorization: Bearer $TOKEN" \
          "$ORCHESTRATOR_URL/health")

        if [ "$STATUS" != "200" ]; then
          echo "FAIL: Health check returned $STATUS"
          exit 1
        fi
        echo "PASS: Orchestrator health check OK (200)"

        echo "=== Smoke test: simple query ==="
        RESPONSE=$(curl -s -w "\n%{http_code}" \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json" \
          -d '{"message": "¿Cuántos sabores tengo?"}' \
          "$ORCHESTRATOR_URL/chat")

        HTTP_CODE=$(echo "$RESPONSE" | tail -1)
        if [ "$HTTP_CODE" != "200" ]; then
          echo "FAIL: Chat endpoint returned $HTTP_CODE"
          exit 1
        fi
        echo "PASS: Chat endpoint OK (200)"
    waitFor:
      - "deploy-workflow-post-write"
      - "deploy-workflow-weekly-summary"
      - "deploy-workflow-low-margin"

substitutions:
  _REGION: "us-central1"
  _REPO: "brewfinance"
  _FUNCTIONS_SA: "bf-functions@${PROJECT_ID}.iam.gserviceaccount.com"
  _ORCHESTRATOR_SA: "bf-orchestrator@${PROJECT_ID}.iam.gserviceaccount.com"
  _WORKFLOW_SA: "bf-workflows@${PROJECT_ID}.iam.gserviceaccount.com"
  _TOOLS_BASE_URL: "https://${_REGION}-${PROJECT_ID}.cloudfunctions.net"

options:
  logging: CLOUD_LOGGING_ONLY
```

---

## 9.4 Manejo de Variables y Secrets

### Variables de entorno (no sensibles)

Se pasan directamente en los comandos de deploy via `--set-env-vars`:

| Variable | Valor | Usado por |
|---|---|---|
| `ENVIRONMENT` | `production` | Orchestrator |
| `TOOLS_BASE_URL` | `https://us-central1-PROJECT.cloudfunctions.net` | Orchestrator, Workflows |
| `REGION` | `us-central1` | Todos |

### Secrets (sensibles)

Se almacenan en **Google Secret Manager** y se inyectan en tiempo de deploy via `--set-secrets`:

| Secret | Descripción | Usado por |
|---|---|---|
| `brewfinance-gemini-key` | API Key de Vertex AI (Gemini) | Orchestrator (Cloud Run) |
| `brewfinance-sheet-id` | ID del Google Spreadsheet | Cloud Functions (reader, writer) |
| `brewfinance-sa-key` | Service account key para Sheets API | Cloud Functions |

### Principio: ningún secret en código

```
✗ Hardcodeado en código         → NUNCA
✗ En variables de Cloud Build   → NUNCA (son visibles en logs)
✗ En .env commiteado a Git      → NUNCA
✓ En Secret Manager             → SIEMPRE
✓ Inyectado via --set-secrets   → En deploy time, no build time
```

---

## 9.5 Tests Automáticos

### Estructura de tests

```
tests/
├── unit/
│   ├── test_guardrails.py          # Validación de parámetros de tools
│   ├── test_context_manager.py     # Construcción del context window
│   ├── test_calculator_ops.py      # Operaciones del calculator
│   └── test_report_templates.py    # Generación de reportes
├── integration/
│   ├── test_sheets_reader.py       # Lectura del mock API
│   ├── test_sheets_writer.py       # Escritura + idempotencia
│   ├── test_react_loop.py          # Ciclo ReAct completo con mock LLM
│   └── test_workflow_trigger.py    # Disparo de workflows
└── smoke/
    ├── test_health.py              # Health check post-deploy
    └── test_simple_query.py        # Query básica end-to-end
```

### Qué valida cada nivel

| Nivel | Qué prueba | Dependencias externas | Cuándo corre |
|---|---|---|---|
| **Unit** | Lógica de negocio aislada (guardrails, cálculos, templates) | Ninguna (mocks) | CI — cada push |
| **Integration** | Interacción entre orchestrator y tools (mock API) | Mock Sheets API (local) | CI — cada push |
| **Smoke** | Sistema desplegado funciona end-to-end | Todos (producción) | CD — post-deploy |

### Ejemplo: test de guardrails

```python
# tests/unit/test_guardrails.py
import pytest
from src.agent.guardrails import validate_tool_call

class TestGuardrails:
    def test_valid_sale_registration(self):
        tool_call = {
            "name": "sheets_writer",
            "args": {
                "hoja": "Ventas",
                "registro": {
                    "sabor": "mango",
                    "cantidad": 10,
                    "precio_unitario": 45.00,
                    "presentacion": "345ml",
                    "canal": "gimnasio",
                    "fecha": "2026-06-15"
                },
                "idempotency_key": "v-20260615-mango-10"
            }
        }
        result = validate_tool_call(tool_call)
        assert result.is_valid is True

    def test_reject_negative_quantity(self):
        tool_call = {
            "name": "sheets_writer",
            "args": {
                "hoja": "Ventas",
                "registro": {
                    "sabor": "mango",
                    "cantidad": -5,
                    "precio_unitario": 45.00,
                    "presentacion": "345ml",
                    "canal": "gimnasio",
                    "fecha": "2026-06-15"
                },
                "idempotency_key": "test-neg"
            }
        }
        result = validate_tool_call(tool_call)
        assert result.is_valid is False
        assert result.error_code == "VALIDATION_FAILED"

    def test_reject_unknown_sabor(self):
        tool_call = {
            "name": "sheets_writer",
            "args": {
                "hoja": "Ventas",
                "registro": {
                    "sabor": "uva",
                    "cantidad": 5,
                    "precio_unitario": 45.00,
                    "presentacion": "345ml",
                    "canal": "gimnasio",
                    "fecha": "2026-06-15"
                },
                "idempotency_key": "test-uva"
            }
        }
        result = validate_tool_call(tool_call)
        assert result.is_valid is False
        assert result.error_code == "UNKNOWN_SABOR"

    def test_reject_write_to_costos(self):
        tool_call = {
            "name": "sheets_writer",
            "args": {
                "hoja": "Costos",
                "registro": {"sabor": "mango", "costo_unitario": 20.0},
                "idempotency_key": "test-costos"
            }
        }
        result = validate_tool_call(tool_call)
        assert result.is_valid is False
        assert result.error_code == "INVALID_SHEET"
```

---

## 9.6 Service Accounts y Permisos (Least Privilege)

Cada componente usa un service account dedicado con permisos mínimos:

| Service Account | Usado por | Permisos |
|---|---|---|
| `bf-functions@` | Cloud Functions (4 tools) | `roles/sheets.editor`, `secretmanager.secretAccessor` |
| `bf-orchestrator@` | Cloud Run (orchestrator) | `roles/cloudfunctions.invoker`, `roles/aiplatform.user`, `secretmanager.secretAccessor`, `workflows.invoker` |
| `bf-workflows@` | Google Workflows | `roles/cloudfunctions.invoker`, `logging.logWriter` |
| `bf-cloudbuild@` | Cloud Build (CI/CD) | `roles/run.admin`, `roles/cloudfunctions.admin`, `roles/workflows.admin`, `artifactregistry.writer` |

---

## 9.7 Diagrama del Pipeline Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                           CI PIPELINE                            │
│                     (cada push / PR)                             │
│                                                                  │
│  ┌──────┐   ┌──────┐   ┌──────────┐   ┌───────┐   ┌────────┐  │
│  │ Lint │──►│ Unit │──►│  Build   │──►│ Trivy │──►│  Push  │  │
│  │ ruff │   │ test │   │  Docker  │   │ scan  │   │ to AR  │  │
│  └──────┘   └──────┘   │ (×3 img) │   │(×3)   │   │        │  │
│                         └──────────┘   └───────┘   └────────┘  │
│                                                                  │
│  Si Trivy encuentra CRITICAL → pipeline FALLA → no se pushea    │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ merge a main
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                           CD PIPELINE                            │
│                     (merge a main)                               │
│                                                                  │
│  ┌───────────────┐   ┌───────────────┐   ┌──────────────────┐  │
│  │ Deploy Cloud  │──►│ Deploy Cloud  │──►│ Deploy Google    │  │
│  │ Functions (×4)│   │ Run (orch.)   │   │ Workflows (×3)   │  │
│  │ en paralelo   │   │               │   │                  │  │
│  └───────────────┘   └───────────────┘   └──────────────────┘  │
│                                                  │               │
│                                                  ▼               │
│                                          ┌──────────────┐       │
│                                          │  Smoke test  │       │
│                                          │  (health +   │       │
│                                          │  simple query)│       │
│                                          └──────────────┘       │
│                                                                  │
│  Si smoke test falla → alerta en Cloud Monitoring                │
└──────────────────────────────────────────────────────────────────┘
```
