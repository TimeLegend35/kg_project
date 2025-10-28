# BGB AI Chat API

Minimalistische AI-Chat-API für BGB-Assistenten mit Thread-Verwaltung, Nachrichtenpersistenz und Streaming-Unterstützung.

## 🚀 Features

- **Thread-Verwaltung**: Threads erstellen, abrufen, auflisten, löschen (soft/hard)
- **Nachrichten**: Verlauf speichern, neue Nachrichten über Agents verarbeiten
- **Streaming**: Server-Sent Events (SSE) für Token-Streaming
- **Agent-Integration**: Nutzt vorhandene Agents aus `langchain_service` (Qwen, Gemini)
- **PostgreSQL-Persistenz**: SQLAlchemy 2.x + Alembic Migrationen
- **Auth**: API-Key oder JWT
- **Observability**: Strukturierte Logs, request_id, Metriken

## 🏗️ Architektur

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP/SSE
┌──────▼──────────┐
│   FastAPI       │
│   (Port 8080)   │
├─────────────────┤
│  - Threads      │
│  - Messages     │
│  - Auth         │
└────┬───────┬────┘
     │       │
     │   ┌───▼──────────┐
     │   │ Agent Runner │
     │   │ (langchain)  │
     │   └───┬──────────┘
     │       │
┌────▼───────▼────┐
│   PostgreSQL    │
│   (Port 5432)   │
└─────────────────┘
```

Die API ruft **keine** direkten Upstream-Services (Solr/Blazegraph) auf. Alle Intelligenz erfolgt über die Agents.

## 📦 Installation & Start

### Voraussetzungen

- Docker & Docker Compose
- Python 3.11+ (für lokale Entwicklung)

### Mit Docker Compose (empfohlen)

```bash
# Services starten (PostgreSQL + API)
docker-compose up -d postgres api

# Logs verfolgen
docker-compose logs -f api

# Migration manuell ausführen (falls nötig)
docker-compose exec api alembic upgrade head
```

Die API läuft auf **http://localhost:8080**

### Lokale Entwicklung

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen setzen
export DB_URL="postgresql+psycopg://bgb_user:bgb_password@localhost:5432/bgb_chat"
export API_KEY="dev-api-key"
export LOG_LEVEL="INFO"

# PostgreSQL starten (falls nicht via Docker)
docker-compose up -d postgres

# Migrationen ausführen
alembic upgrade head

# API starten
uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

## 🔑 Authentication

API-Key über Header:
```bash
X-API-Key: dev-api-key-change-me
```

Oder JWT Bearer Token:
```bash
Authorization: Bearer <token>
```

Im Dev-Modus (wenn `API_KEY` nicht gesetzt): keine Auth erforderlich.

## 📡 API-Endpunkte

### Health & Meta

- `GET /healthz` - Health Check
- `GET /readyz` - Readiness Check
- `GET /version` - Version Info

### Threads

- `POST /api/v1/threads` - Thread erstellen
- `GET /api/v1/threads/{thread_id}` - Thread abrufen
- `GET /api/v1/threads?limit=50&cursor=<timestamp>` - Threads auflisten (Pagination)
- `DELETE /api/v1/threads/{thread_id}?hard=false` - Thread löschen (soft/hard)

### Messages

- `GET /api/v1/threads/{thread_id}/messages?limit=100&before_id=<id>` - Nachrichten auflisten
- `POST /api/v1/threads/{thread_id}/messages` - Nachricht senden (Agent aufrufen)

### Agents

- `GET /api/v1/agents` - Verfügbare Agents auflisten

## 🧪 Beispiele

### Thread erstellen

```bash
curl -X POST http://localhost:8080/api/v1/threads \
  -H "X-API-Key: dev-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Frage zu Tierhalterhaftung",
    "metadata": {"topic": "bgb-paragraph-833"}
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Frage zu Tierhalterhaftung",
  "metadata": {"topic": "bgb-paragraph-833"},
  "created_at": "2025-10-25T12:00:00Z",
  "updated_at": "2025-10-25T12:00:00Z",
  "deleted_at": null
}
```

### Nachricht senden (non-stream)

```bash
curl -X POST http://localhost:8080/api/v1/threads/550e8400-e29b-41d4-a716-446655440000/messages \
  -H "X-API-Key: dev-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "qwen",
    "input": "Mein Hund hat eine Vase zerbrochen. Muss ich zahlen?",
    "stream": false
  }'
```

Response:
```json
{
  "message": {
    "id": 1,
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "assistant",
    "content": "Ja, nach § 833 BGB...",
    "agent_name": "qwen",
    "tool_calls": [...],
    "usage": null,
    "created_at": "2025-10-25T12:00:05Z"
  },
  "usage": null,
  "tool_calls": [...],
  "meta": {"agent": "qwen"}
}
```

### Nachricht senden (streaming)

```bash
curl -X POST http://localhost:8080/api/v1/threads/550e8400-e29b-41d4-a716-446655440000/messages \
  -H "X-API-Key: dev-api-key-change-me" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "agent": "qwen",
    "input": "Was besagt § 833 BGB?",
    "stream": true
  }'
```

Response (SSE):
```
event: message
data: {"role":"assistant","partial":true}

event: token
data: {"token":"Ja, "}

event: token
data: {"token":"nach § 833"}

event: token
data: {"token":" BGB..."}

event: done
data: {"final":true,"content":"Ja, nach § 833 BGB...","message_id":2}
```

### Threads auflisten

```bash
curl http://localhost:8080/api/v1/threads?limit=10 \
  -H "X-API-Key: dev-api-key-change-me"
```

### Nachrichten auflisten

```bash
curl http://localhost:8080/api/v1/threads/550e8400-e29b-41d4-a716-446655440000/messages \
  -H "X-API-Key: dev-api-key-change-me"
```

### Verfügbare Agents

```bash
curl http://localhost:8080/api/v1/agents \
  -H "X-API-Key: dev-api-key-change-me"
```

Response:
```json
{
  "agents": [
    {
      "name": "qwen",
      "description": "Qwen-based BGB assistant with function calling",
      "available": true
    },
    {
      "name": "gemini",
      "description": "Google Gemini-based BGB assistant",
      "available": true
    }
  ]
}
```

## 🔧 Konfiguration

Umgebungsvariablen:

```bash
# Database
DB_URL=postgresql+psycopg://bgb_user:bgb_password@localhost:5432/bgb_chat

# Security
API_KEY=your-secret-api-key
JWT_SECRET=your-jwt-secret

# Agent Service
AGENT_SERVICE_MODE=inproc  # oder "http"
AGENT_SERVICE_URL=http://agent-service:9000  # wenn mode=http

# Timeouts
AGENT_CALL_TIMEOUT_MS=120000  # 2 Minuten

# Logging
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```

## 📊 Datenbankschema

### Threads
- `id` (UUID, PK)
- `title` (String, optional)
- `metadata` (JSONB, optional)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)
- `deleted_at` (Timestamp, nullable)

### Messages
- `id` (BigInt, PK, Auto)
- `thread_id` (UUID, FK → threads.id, CASCADE)
- `role` (Enum: user, assistant, tool)
- `content` (Text)
- `agent_name` (String, optional)
- `tool_calls` (JSONB, optional)
- `usage` (JSONB, optional)
- `created_at` (Timestamp)

Indizes:
- `threads(updated_at)`
- `threads(deleted_at)`
- `messages(thread_id, created_at)`

## 🧩 Projektstruktur

```
api/
├── __init__.py
├── main.py                 # FastAPI App
├── core/
│   ├── config.py           # Settings
│   ├── errors.py           # Error handling
│   └── logging.py          # Structured logging
├── routes/
│   ├── health.py           # Health checks
│   ├── threads.py          # Thread endpoints
│   ├── messages.py         # Message endpoints (+ SSE)
│   └── agents.py           # Agent info
├── services/
│   ├── chat.py             # Agent runner integration
│   └── auth.py             # Authentication
├── store/
│   ├── models.py           # SQLAlchemy models
│   ├── database.py         # DB connection
│   └── repository.py       # Data access layer
└── schemas/
    └── schemas.py          # Pydantic schemas

migrations/
├── env.py                  # Alembic environment
├── script.py.mako          # Migration template
└── versions/
    └── 001_initial_schema.py

langchain_service/          # Existing agents (not modified)
├── qwen_agent_bgb.py
├── gemini_agent_bgb.py
└── tools.py
```

## 🧪 Tests

(TODO: Implementierung von Unit-, Integration- und E2E-Tests)

```bash
# Unit tests
pytest tests/unit/

# Integration tests (mit Test-DB-Container)
pytest tests/integration/

# E2E tests (SSE-Streaming)
pytest tests/e2e/
```

## 🐛 Troubleshooting

### Database connection failed
```bash
# PostgreSQL läuft?
docker-compose ps postgres

# Logs checken
docker-compose logs postgres

# Migration manuell ausführen
docker-compose exec api alembic upgrade head
```

### Agent not available
```bash
# Qwen: Ollama läuft? Model installiert?
ollama serve
ollama pull qwen2.5:14b

# Gemini: API-Key gesetzt?
export GOOGLE_API_KEY="your-key"
```

### SSE stream not working
- Nginx buffering deaktivieren: `proxy_buffering off;`
- Browser DevTools → Network → EventStream prüfen

## 📝 API-Dokumentation

Interaktive Docs verfügbar unter:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 🛡️ Sicherheit

- ✅ API-Key/JWT Authentication
- ✅ Input-Validierung (Pydantic)
- ✅ SQL-Injection-Schutz (SQLAlchemy ORM)
- ✅ Rate Limiting (TODO: Redis-basiert)
- ✅ Content-Size-Limits (16KB input, 8KB params)
- ⚠️ CORS: Für Produktion einschränken
- ⚠️ Secrets: In Produktion über Secret Manager

## 📈 Nächste Schritte

- [ ] Echtes Token-Streaming von Agents implementieren
- [ ] Redis für Rate-Limiting & Caching integrieren
- [ ] Prometheus-Metriken exportieren
- [ ] Umfassende Tests schreiben
- [ ] CI/CD Pipeline (GitHub Actions)
- [ ] Production-ready Secrets Management
- [ ] Helm Chart für Kubernetes

## 📄 Lizenz

(Projektlizenz hier angeben)

## 🤝 Contribution

Siehe CONTRIBUTING.md (TODO)

