# PROYECTO 3 – Sección 4: Contenerización con Docker

**Proyecto:** LLM Agentic Architecture with Serverless Tools Integration  
**Curso:** Diseño de Infraestructura Escalable — BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Estudiante:** Francisco

---

## 4.1 Servicios a Contenerizar

El sistema BrewFinance Agent se compone de 3 servicios propios que se contenerizarán de forma independiente:

| Servicio | Tecnología | Función | Puerto |
|---|---|---|---|
| **orchestrator** | Python 3.12 + FastAPI | Backend principal: recibe mensajes del usuario, ejecuta el ciclo ReAct, coordina tool calls y devuelve respuestas | 8000 |
| **mock-sheets-api** | Python 3.12 + FastAPI | API simulada de Google Sheets para desarrollo y testing local (CRUD de ventas, costos, gastos) | 8001 |
| **logging-service** | Python 3.12 + FastAPI | Servicio auxiliar que recibe y almacena logs estructurados del agente (traces ReAct, tool calls, errores) | 8002 |

---

## 4.2 Dockerfile del Orchestrator (Multi-stage, Non-root, Liviano)

```dockerfile
# ============================================
# STAGE 1: Builder — instala dependencias
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Copiar solo requirements primero (cache de capas)
COPY requirements.txt .

# Instalar dependencias en directorio aislado
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================
# STAGE 2: Runtime — imagen final liviana
# ============================================
FROM python:3.12-slim AS runtime

# Metadatos
LABEL maintainer="francisco@brewfinance.local"
LABEL description="BrewFinance Agent Orchestrator"
LABEL version="1.0.0"

# Crear usuario non-root
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copiar dependencias desde builder
COPY --from=builder /install /usr/local

# Copiar código fuente
COPY src/ ./src/
COPY config/ ./config/

# Asignar permisos al usuario non-root
RUN chown -R appuser:appgroup /app

# Cambiar a usuario non-root
USER appuser

# Variables de entorno (no secrets — esos vienen externos)
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Exponer puerto
EXPOSE 8000

# Ejecutar con uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### requirements.txt del Orchestrator

```txt
fastapi==0.115.0
uvicorn==0.32.0
google-genai==1.10.0
google-auth==2.35.0
httpx==0.27.0
pydantic==2.9.0
python-dotenv==1.0.1
structlog==24.4.0
```

---

## 4.3 Dockerfile del Mock Sheets API

```dockerfile
# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements-mock.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-mock.txt

# ============================================
# STAGE 2: Runtime
# ============================================
FROM python:3.12-slim AS runtime

LABEL description="BrewFinance Mock Sheets API"
LABEL version="1.0.0"

RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY mock_api/ ./mock_api/
COPY data/ ./data/

RUN chown -R appuser:appgroup /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PORT=8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

EXPOSE 8001

CMD ["uvicorn", "mock_api.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## 4.4 Dockerfile del Logging Service

```dockerfile
# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements-logging.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-logging.txt

# ============================================
# STAGE 2: Runtime
# ============================================
FROM python:3.12-slim AS runtime

LABEL description="BrewFinance Logging Service"
LABEL version="1.0.0"

RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY logging_service/ ./logging_service/

# Directorio para logs locales (writable por non-root)
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PORT=8002

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" || exit 1

EXPOSE 8002

CMD ["uvicorn", "logging_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

---

## 4.5 Docker Compose (Desarrollo Local)

```yaml
version: "3.9"

services:
  orchestrator:
    build:
      context: .
      dockerfile: docker/Dockerfile.orchestrator
    container_name: brewfinance-orchestrator
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - MOCK_SHEETS_URL=http://mock-sheets-api:8001
      - LOGGING_URL=http://logging-service:8002
    env_file:
      - .env  # Secrets externos (GOOGLE_API_KEY, etc.)
    depends_on:
      mock-sheets-api:
        condition: service_healthy
      logging-service:
        condition: service_healthy
    networks:
      - brewfinance-net
    restart: unless-stopped

  mock-sheets-api:
    build:
      context: .
      dockerfile: docker/Dockerfile.mock-api
    container_name: brewfinance-mock-sheets
    ports:
      - "8001:8001"
    volumes:
      - ./data:/app/data:ro  # Datos de prueba (read-only)
    networks:
      - brewfinance-net
    restart: unless-stopped

  logging-service:
    build:
      context: .
      dockerfile: docker/Dockerfile.logging
    container_name: brewfinance-logging
    ports:
      - "8002:8002"
    volumes:
      - logs-data:/app/logs  # Volumen persistente para logs
    networks:
      - brewfinance-net
    restart: unless-stopped

networks:
  brewfinance-net:
    driver: bridge

volumes:
  logs-data:
```

---

## 4.6 Estructura del Proyecto

```
brewfinance-agent/
├── docker/
│   ├── Dockerfile.orchestrator
│   ├── Dockerfile.mock-api
│   └── Dockerfile.logging
├── src/                          # Orchestrator
│   ├── main.py                   # FastAPI app + endpoints
│   ├── agent/
│   │   ├── react_loop.py         # Ciclo ReAct principal
│   │   ├── tool_router.py        # Selección y despacho de tools
│   │   └── guardrails.py         # Validación pre-ejecución
│   ├── llm/
│   │   ├── gemini_client.py      # Cliente Vertex AI / Gemini
│   │   └── prompts.py            # System prompt + tool schemas
│   └── models/
│       ├── schemas.py            # Pydantic models (request/response)
│       └── errors.py             # Códigos de error estandarizados
├── mock_api/                     # Mock Sheets API
│   ├── main.py
│   ├── routes/
│   │   ├── ventas.py
│   │   ├── costos.py
│   │   └── gastos.py
│   └── storage.py                # In-memory storage con datos de prueba
├── logging_service/              # Logging Service
│   ├── main.py
│   └── handlers.py
├── config/
│   └── tools_schema.json         # Definiciones de tools para el LLM
├── data/                         # Datos de prueba (CSV)
│   ├── ventas_sample.csv
│   ├── costos_sample.csv
│   └── gastos_sample.csv
├── tests/
│   ├── test_orchestrator.py
│   ├── test_mock_api.py
│   └── test_guardrails.py
├── docker-compose.yml
├── requirements.txt
├── requirements-mock.txt
├── requirements-logging.txt
├── .env.example                  # Template de secrets (sin valores reales)
├── .dockerignore
└── README.md
```

---

## 4.7 Manejo de Secrets Externos

Los secrets nunca se incluyen en las imágenes Docker ni en el código fuente.

| Secret | Uso | Mecanismo en desarrollo | Mecanismo en producción |
|---|---|---|---|
| `GOOGLE_API_KEY` | Autenticación con Vertex AI (Gemini) | Archivo `.env` (excluido de Git via `.gitignore`) | GCP Secret Manager → inyectado como variable de entorno en Cloud Run |
| `SHEETS_SERVICE_ACCOUNT` | Credencial de servicio para Google Sheets API | Archivo JSON local montado como volumen | GCP Secret Manager → montado como archivo en Cloud Run |
| `LOGGING_API_KEY` | Autenticación entre orchestrator y logging service | Archivo `.env` | Variable de entorno en Cloud Run (servicio interno, sin acceso público) |

### .env.example (template sin valores)

```env
# Google Vertex AI
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CLOUD_PROJECT=your_project_id

# Google Sheets
SHEETS_SPREADSHEET_ID=your_spreadsheet_id
SHEETS_SERVICE_ACCOUNT_PATH=/app/secrets/service_account.json

# Logging
LOGGING_API_KEY=your_logging_key_here

# Environment
ENVIRONMENT=development
```

### .dockerignore

```
.env
*.pyc
__pycache__
.git
.gitignore
*.md
tests/
.venv/
*.json.key
secrets/
```

---

## 4.8 Vulnerability Scanning

### Herramienta seleccionada: Trivy

Trivy es un scanner open-source de vulnerabilidades para imágenes Docker, mantenido por Aqua Security.

### Comando de escaneo

```bash
# Escanear imagen del orchestrator
trivy image brewfinance-orchestrator:latest

# Escanear con severidad mínima HIGH
trivy image --severity HIGH,CRITICAL brewfinance-orchestrator:latest

# Escanear todas las imágenes del proyecto
for img in orchestrator mock-sheets logging; do
  echo "=== Scanning brewfinance-$img ==="
  trivy image --severity HIGH,CRITICAL brewfinance-$img:latest
done
```

### Integración con CI/CD

```yaml
# Paso en pipeline CI (GitHub Actions / Cloud Build)
- name: Scan Docker image
  run: |
    trivy image --exit-code 1 --severity CRITICAL brewfinance-orchestrator:latest
```

Si Trivy encuentra vulnerabilidades CRITICAL, el pipeline falla y no se despliega.

### Buenas prácticas implementadas

| Práctica | Implementación |
|---|---|
| Imágenes base livianas | `python:3.12-slim` (~50MB vs ~900MB de `python:3.12`) |
| Multi-stage builds | Stage 1 (builder) instala dependencias, Stage 2 (runtime) solo copia lo necesario |
| Usuario non-root | `appuser` sin shell, sin home, sin privilegios de escritura fuera de `/app` |
| Sin secrets en imagen | Secrets vía `.env` (dev) o Secret Manager (prod), nunca en `COPY` o `ENV` |
| `.dockerignore` | Excluye `.env`, tests, `.git`, secretos locales |
| Health checks | Cada contenedor expone `/health` y Docker valida disponibilidad |
| Pinning de versiones | Dependencias con versión exacta en requirements.txt |
| No cache de pip | `--no-cache-dir` elimina archivos temporales de instalación |

---

## 4.9 Comparativa de Tamaños de Imagen

| Imagen | Base | Tamaño estimado |
|---|---|---|
| `brewfinance-orchestrator` | python:3.12-slim (multi-stage) | ~120 MB |
| `brewfinance-mock-sheets` | python:3.12-slim (multi-stage) | ~90 MB |
| `brewfinance-logging` | python:3.12-slim (multi-stage) | ~80 MB |
| (si se usara) python:3.12 sin slim | python:3.12 (single-stage) | ~950 MB |

La estrategia multi-stage + slim reduce el tamaño total del stack de ~2.8 GB a ~290 MB (~90% de reducción).
