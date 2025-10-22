# BGB Chat Service

AI-powered Legal Chat Service für das deutsche BGB mit FastAPI und Qwen-Agent.

## 🎯 Features

- ✅ **Streaming Chat** mit Server-Sent Events (SSE)
- ✅ **Tool Calls** transparent zum Frontend
- ✅ **Chat Persistence** mit PostgreSQL
- ✅ **Session Management** für Multi-User
- ✅ **CORS-enabled** für Next.js Frontend
- ✅ **Health Checks** für alle Services

## 🏗️ Architektur

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Next.js     │  SSE    │  FastAPI     │  SQL    │  PostgreSQL  │
│  Frontend    │◀───────▶│  Backend     │◀───────▶│  Checkpoints │
└──────────────┘         └──────────────┘         └──────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  Qwen Agent  │
                         │  + Tools     │
                         └──────────────┘
```

## 📦 Installation

```bash
# 1. Dependencies installieren
cd packages/chat_service
pip install -r requirements.txt

# 2. Environment Setup
cp .env.example .env
# .env anpassen

# 3. PostgreSQL starten
cd ../..
docker-compose up -d postgres

# 4. API starten
cd packages/chat_service
python -m uvicorn chat_api.main:app --reload --port 8000
```

## 🚀 Quick Start

```bash
# Health Check
curl http://localhost:8000/health

# Neue Session erstellen
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "title": "BGB Fragen"}'

# Chat Stream
curl -N http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "message": "Was ist ein Kaufvertrag?"}'
```

## 📚 API Dokumentation

Nach dem Start verfügbar unter:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Entwicklung

```bash
# Tests ausführen
pytest

# Linting
ruff check .

# Formatting
black .
```

## 📝 Environment Variables

```bash
# API
API_HOST=0.0.0.0
API_PORT=8000

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bgb_chat
POSTGRES_USER=bgb_user
POSTGRES_PASSWORD=your_password

# Qwen Agent
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:14B

# External Services
SOLR_URL=http://localhost:8984/solr/bgb_core
BLAZEGRAPH_URL=http://localhost:9999/bigdata/sparql

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```

## 🏛️ Monorepo Integration

Dieses Package ist Teil des BGB Knowledge Graph Projekts:

```
kg_project/
├── packages/
│   └── chat_service/          # 👈 Dieses Package
├── kg_curation/               # Knowledge Graph Erstellung
├── kg_search_index/           # Solr Index
├── langchain_service/         # Shared Tools & Agent
└── docker-compose.yml         # Shared Services
```

## 📖 Weitere Dokumentation

- [API Endpoints](./docs/API.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Frontend Integration](./docs/FRONTEND.md)

