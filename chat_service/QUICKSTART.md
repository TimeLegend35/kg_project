# 🚀 BGB Chat Service - Quick Reference

## 📋 Schnellstart

### 1. Setup
```bash
cd packages/chat_service
./setup.sh
```

### 2. Starten
```bash
./start.sh
```

### 3. Testen
```bash
# Health Check
curl http://localhost:8000/health

# Session erstellen
SESSION_RESPONSE=$(curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "title": "Test Chat"}')

# Session ID extrahieren
SESSION_ID=$(echo $SESSION_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")

# Chat starten
curl -N http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Was ist ein Kaufvertrag?\"}"
```

## 📡 API Endpoints

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/` | Root Info |
| GET | `/docs` | Swagger UI |
| GET | `/health` | Health Check |
| GET | `/health/detailed` | Detailed Health |
| POST | `/sessions` | Create Session |
| GET | `/sessions` | List Sessions |
| GET | `/sessions/{id}` | Get Session |
| POST | `/chat/stream` | Stream Chat (SSE) |
| GET | `/chat/{id}/history` | Get History |

## 🔧 Konfiguration

Bearbeite `.env`:

```bash
# Ollama Model ändern
OLLAMA_MODEL=qwen3:14B

# Thinking Mode aktivieren/deaktivieren
ENABLE_THINKING=true

# CORS für Frontend
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

## 🐛 Debugging

```bash
# Logs anzeigen
docker-compose logs -f bgb-postgres

# PostgreSQL testen
docker exec -it bgb-postgres psql -U bgb_user -d bgb_chat

# Tabellen anzeigen
docker exec -it bgb-postgres psql -U bgb_user -d bgb_chat -c "\dt"
```

## 📦 Dependencies aktualisieren

```bash
pip install -r requirements.txt --upgrade
```

## 🧪 Tests

```bash
pytest
pytest -v  # Verbose
pytest --cov  # Mit Coverage
```

## 🔄 Service neu starten

```bash
# API neu starten
./start.sh

# PostgreSQL neu starten
cd ../..
docker-compose restart bgb-postgres
```

## ⚠️ Troubleshooting

### PostgreSQL Connection Failed
```bash
# Status prüfen
docker-compose ps bgb-postgres

# Neu starten
docker-compose restart bgb-postgres

# Logs prüfen
docker-compose logs bgb-postgres
```

### Ollama nicht erreichbar
```bash
# Ollama Status
curl http://localhost:11434/api/tags

# Ollama starten (falls lokal installiert)
ollama serve
```

### Port bereits belegt
```bash
# Port 8000 freigeben (macOS)
lsof -ti:8000 | xargs kill -9

# Oder anderen Port verwenden
uvicorn chat_api.main:app --port 8001
```

## 📚 Weitere Infos

- [Vollständige README](README.md)
- [Monorepo Übersicht](../../MONOREPO_README.md)
- [API Dokumentation](http://localhost:8000/docs)

