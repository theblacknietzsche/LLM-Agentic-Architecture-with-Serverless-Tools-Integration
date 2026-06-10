# BrewFinance Agent

Agente conversacional de inteligencia financiera para microempresas de bebidas artesanales.

## Arquitectura

- **Orchestrator:** FastAPI + Gemini 2.5 Flash (ReAct pattern)
- **Tools:** 4 Cloud Functions (sheets_reader, sheets_writer, calculator, report_generator)
- **Data Store:** Google Sheets
- **Workflows:** Google Workflows (post_write_check, weekly_summary, low_margin_alert)
- **Observabilidad:** Cloud Logging + Cloud Trace + Cloud Monitoring

## Requisitos

- Python 3.12+
- Docker & Docker Compose
- Google Cloud SDK (para deploy)
- Cuenta de GCP con Vertex AI habilitado

## Inicio rápido (desarrollo local)

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/brewfinance-agent.git
cd brewfinance-agent

# 2. Copiar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 3. Levantar con Docker Compose
docker compose up --build

# 4. Probar el agente
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{"message": "¿Cuál es mi sabor más rentable?"}'
```

## Estructura del proyecto

```
brewfinance-agent/
├── src/                        # Orchestrator (FastAPI)
├── mock_api/                   # Mock Sheets API para desarrollo
├── logging_service/            # Servicio de logging
├── cloud_functions/            # Cloud Functions (4 tools)
├── config/                     # Configuración y tool schemas
├── data/                       # Datos de prueba (CSV)
├── docker/                     # Dockerfiles
├── workflows/                  # Google Workflows (YAML)
├── tests/                      # Tests (unit, integration, smoke)
├── docker-compose.yml
└── README.md
```

## Tests

```bash
# Tests unitarios
pytest tests/unit/ -v

# Tests de integración (requiere mock API corriendo)
docker compose up mock-sheets-api -d
pytest tests/integration/ -v

# Todos los tests
pytest tests/ -v
```

## Deploy a GCP

```bash
# Autenticarse
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy Cloud Functions
gcloud builds submit --config=cloudbuild-cd.yaml

# O deploy manual de cada componente
gcloud functions deploy bf-sheets-reader --gen2 --runtime=python312 ...
gcloud run deploy brewfinance-orchestrator --image=... 
```

## Curso

**Proyecto 3** — LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute
