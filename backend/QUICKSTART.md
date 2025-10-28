# 🎯 BGB AI Chat API - Schnellstart

Die minimalistische Chat-API für BGB-Assistenten ist vollständig implementiert!

## ✅ Was wurde erstellt?

### 1️⃣ **Core-Infrastruktur**
- ✅ FastAPI-Anwendung mit strukturiertem Logging
- ✅ PostgreSQL-Integration (SQLAlchemy 2.x + Alembic)
- ✅ Konfigurationsmanagement (Environment-basiert)
- ✅ Fehlerbehandlung (konsistente Error-Responses)
- ✅ Auth-Middleware (API-Key + JWT)

### 2️⃣ **Datenbankschicht**
- ✅ ORM-Modelle: `Thread` + `Message`
- ✅ Repository-Pattern für saubere Datenzugriffe
- ✅ Alembic-Migrationen (initiales Schema)
- ✅ JSONB für strukturierte Daten (metadata, tool_calls, usage)
- ✅ Indizes für Performance

### 3️⃣ **API-Endpunkte**
- ✅ Threads: CRUD + Pagination + Soft/Hard-Delete
- ✅ Messages: List + Create (ruft Agents auf)
- ✅ Streaming: SSE-Support für Token-Streaming
- ✅ Agents: Liste verfügbarer Agents
- ✅ Health: /healthz, /readyz, /version

### 4️⃣ **Agent-Integration**
- ✅ Zentraler `run_agent()` Service
- ✅ Integration mit `langchain_service` (Qwen + Gemini)
- ✅ Vollständiger Verlauf wird an Agents übergeben
- ✅ Tool-Calls + Usage werden persistiert

### 5️⃣ **DevOps**
- ✅ Docker Compose (PostgreSQL + API)
- ✅ Dockerfile (Multi-Stage, Non-Root User)
- ✅ Migrations laufen automatisch beim Start
- ✅ Health Checks + Graceful Shutdown

## 🚀 So starten Sie die API:

### Option 1: Mit Docker Compose (empfohlen)

```bash
# Quick Start
./start_api.sh

# Oder manuell:
docker-compose up -d postgres api

# Logs verfolgen
docker-compose logs -f api
```

Die API läuft dann auf **http://localhost:8080**

### Option 2: Lokal (für Entwicklung)

```bash
# Umgebungsvariablen setzen
cp .env.example .env

# PostgreSQL starten
docker-compose up -d postgres

# Dependencies installieren
pip install -r requirements.txt

# Migrationen ausführen
alembic upgrade head

# API starten
uvicorn api.main:app --reload --port 8080
```

## 🧪 Tests ausführen:

```bash
# Integration-Tests
python test_api.py

# Oder manuell testen:
curl http://localhost:8080/healthz
curl -H "X-API-Key: dev-api-key-change-me" \
     http://localhost:8080/api/v1/agents
```

## 📚 Dokumentation:

- **API-Dokumentation**: Siehe `API_README.md`
- **Interaktive Docs**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## 🎯 Beispiel-Workflow:

```bash
# 1. Thread erstellen
THREAD_ID=$(curl -X POST http://localhost:8080/api/v1/threads \
  -H "X-API-Key: dev-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"title":"Tierhalterhaftung"}' | jq -r '.id')

# 2. Nachricht senden (non-stream)
curl -X POST http://localhost:8080/api/v1/threads/$THREAD_ID/messages \
  -H "X-API-Key: dev-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "qwen",
    "input": "Mein Hund hat eine Vase zerbrochen. Muss ich zahlen?",
    "stream": false
  }'

# 3. Nachrichtenverlauf abrufen
curl http://localhost:8080/api/v1/threads/$THREAD_ID/messages \
  -H "X-API-Key: dev-api-key-change-me"

# 4. Streaming (SSE)
curl -X POST http://localhost:8080/api/v1/threads/$THREAD_ID/messages \
  -H "X-API-Key: dev-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "qwen",
    "input": "Was sind die Details zu § 833 BGB?",
    "stream": true
  }'
```

## 📁 Projektstruktur:

```
api/
├── main.py                 # FastAPI App
├── core/                   # Config, Errors, Logging
├── routes/                 # API Endpoints
├── services/               # Business Logic (Agent-Integration)
├── store/                  # Database (Models, Repository)
└── schemas/                # Pydantic Schemas

migrations/                 # Alembic Migrationen
├── env.py
├── versions/
│   └── 001_initial_schema.py

docker-compose.yml          # PostgreSQL + API
Dockerfile                  # API Container
requirements.txt            # Python Dependencies
alembic.ini                 # Alembic Config
```

## 🔑 Wichtige Hinweise:

1. **Agent-Verfügbarkeit**: 
   - Qwen benötigt Ollama: `ollama serve` + `ollama pull qwen2.5:14b`
   - Gemini benötigt: `export GOOGLE_API_KEY="your-key"`

2. **Keine direkten Upstream-Calls**: 
   - API ruft nur Agents auf
   - Agents nutzen Tools (Solr/Blazegraph)
   - Saubere Trennung der Verantwortlichkeiten

3. **Streaming**: 
   - Aktuell: Simulated Streaming (Response wird gesplittet)
   - TODO: Echtes Token-Streaming wenn Agents es unterstützen

4. **Production-Ready**:
   - ⚠️ Secrets ändern (`API_KEY`, `JWT_SECRET`, DB-Passwort)
   - ⚠️ CORS konfigurieren
   - ⚠️ Rate-Limiting aktivieren (Redis)
   - ⚠️ Monitoring/Metrics hinzufügen

## 🐛 Troubleshooting:

```bash
# API-Logs
docker-compose logs -f api

# Database-Logs
docker-compose logs -f postgres

# Migration manuell ausführen
docker-compose exec api alembic upgrade head

# Container neu bauen
docker-compose build api
docker-compose up -d api
```

## 📊 Nächste Schritte:

- [ ] Echtes Token-Streaming implementieren
- [ ] Redis für Rate-Limiting
- [ ] Umfassende Tests (Unit, Integration, E2E)
- [ ] Prometheus-Metriken
- [ ] Kubernetes Deployment (Helm)

---

**Viel Erfolg! 🚀**

Bei Fragen siehe `API_README.md` oder FastAPI Docs unter `/docs`

