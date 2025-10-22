# 🎯 BGB Knowledge Graph Project - Monorepo

AI-powered Legal Assistant für das deutsche Bürgerliche Gesetzbuch (BGB) mit Knowledge Graph, Semantic Search und Chat Interface.

## 📦 Monorepo-Struktur

```
kg_project/                          # Root Monorepo
├── packages/                        # 🆕 Monorepo Packages
│   └── chat_service/                # FastAPI Chat Service (eigenständiges Package)
│       ├── chat_api/                # API Implementation
│       ├── tests/                   # Tests
│       ├── requirements.txt         # Dependencies
│       ├── pyproject.toml          # Package Config
│       └── setup.sh                # Setup Script
│
├── kg_curation/                     # Knowledge Graph Erstellung
│   ├── build_graph.py              # Graph Builder
│   ├── model.py                    # Ontology Model
│   └── transform_raw_data.py       # Data Transformation
│
├── kg_search_index/                 # Solr Search Index
│   ├── build_solr_index.py        # Index Builder
│   └── query_bgb.py                # Search Queries
│
├── langchain_service/               # 🔧 Shared: Qwen Agent & Tools
│   ├── qwen_agent_bgb.py           # Qwen Agent Implementation
│   └── tools.py                    # Solr & SPARQL Tools
│
├── blazegraph_instance/             # Blazegraph Loader
├── lib/                            # Frontend Libraries
├── docker-compose.yml              # 🐳 All Services
├── Pipfile                         # Root Dependencies
└── README.md                       # 👈 Diese Datei
```

## 🏗️ Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│                 (Next.js - in development)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/SSE
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Chat Service (FastAPI)                         │
│              packages/chat_service/chat_api                      │
│  • Streaming Chat (SSE)  • Session Management  • Persistence    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Qwen Agent (langchain_service)                  │
│              • Function Calling  • Thinking Mode                 │
└─────────────┬───────────────────────────────┬───────────────────┘
              │                               │
    ┌─────────▼─────────┐         ┌─────────▼──────────┐
    │   Solr Search     │         │   SPARQL Query     │
    │  (kg_search_index)│         │  (Blazegraph)      │
    └───────────────────┘         └────────────────────┘
                    │                       │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │  BGB Knowledge Graph  │
                    │   (kg_curation)       │
                    └───────────────────────┘
```

## 🚀 Quick Start

### 1. Services starten

```bash
# Alle Docker Services starten
docker-compose up -d

# Status prüfen
docker-compose ps
```

### 2. Chat Service Setup

```bash
# Automatisches Setup
cd packages/chat_service
./setup.sh

# Oder manuell:
pip install -r requirements.txt
cp .env.example .env
```

### 3. Chat API starten

```bash
cd packages/chat_service
python -m uvicorn chat_api.main:app --reload --port 8000
```

### 4. Testen

```bash
# Health Check
curl http://localhost:8000/health/detailed

# Session erstellen
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "title": "BGB Fragen"}'

# Chat starten (kopiere session_id von oben)
curl -N http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "message": "Was ist ein Kaufvertrag?"}'
```

## 📦 Package: Chat Service

Der Chat Service ist als **eigenständiges Package** im Monorepo organisiert:

### Features
✅ **Streaming Chat** mit Server-Sent Events (SSE)  
✅ **Tool Calls** transparent zum Frontend  
✅ **Thinking Mode** für Reasoning Traces  
✅ **Chat Persistence** mit PostgreSQL  
✅ **Session Management** für Multi-User  
✅ **CORS-enabled** für Next.js Frontend  

### API Dokumentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Mehr Details
Siehe [packages/chat_service/README.md](packages/chat_service/README.md)

## 🔧 Services

| Service | Port | Beschreibung |
|---------|------|--------------|
| **Chat API** | 8000 | FastAPI Chat Service |
| **PostgreSQL** | 5432 | Chat Persistence |
| **Solr** | 8984 | Full-text Search |
| **Blazegraph** | 9999 | SPARQL Endpoint |
| **Ollama** | 11434 | Qwen LLM |

## 📚 Dokumentation

### Chat Service (Monorepo Package)
- [Chat Service README](packages/chat_service/README.md)
- [API Endpoints](packages/chat_service/docs/API.md) _(coming soon)_
- [Frontend Integration](packages/chat_service/docs/FRONTEND.md) _(coming soon)_

### Knowledge Graph
- [BGB RDF Exploration](BGB_RDF_Exploration.ipynb)
- [Ontology Model](kg_curation/model.py)

### Search Index
- [Solr Setup](kg_search_index/README.md)

## 🛠️ Entwicklung

### Monorepo-Vorteile
- **Shared Code**: `langchain_service` wird von allen Packages genutzt
- **Unabhängige Deployments**: Jedes Package kann separat deployed werden
- **Gemeinsame Services**: Docker-Compose für alle Services
- **Konsistente Dependencies**: Zentrale Docker-Compose

### Neue Packages hinzufügen

```bash
mkdir -p packages/new_package
cd packages/new_package

# Package-Struktur erstellen
mkdir -p {src,tests,docs}
touch README.md requirements.txt pyproject.toml
```

### Tests ausführen

```bash
# Chat Service Tests
cd packages/chat_service
pytest

# Alle Tests (wenn weitere Packages hinzukommen)
find packages -name "pytest" -exec {} \;
```

## 🐳 Docker Services Management

```bash
# Alle Services starten
docker-compose up -d

# Nur PostgreSQL
docker-compose up -d bgb-postgres

# Nur Solr + Blazegraph
docker-compose up -d bgb-solr bgb-blazegraph

# Logs anzeigen
docker-compose logs -f bgb-postgres

# Services stoppen
docker-compose down

# Mit Volumes löschen
docker-compose down -v
```

## 🔐 Environment Variables

Jedes Package hat eigene `.env` Datei:

```bash
# Chat Service
packages/chat_service/.env

# Root (für andere Services)
.env  # (optional)
```

## 📝 Nächste Schritte

- [ ] Frontend (Next.js) als weiteres Package hinzufügen
- [ ] PostgreSQL Persistence vollständig implementieren
- [ ] Session Management mit CRUD-Operationen
- [ ] Tests erweitern
- [ ] CI/CD Pipeline aufsetzen
- [ ] Deployment-Dokumentation

## 🤝 Contributing

1. Branch erstellen: `git checkout -b feature/my-feature`
2. Changes committen: `git commit -am 'Add feature'`
3. Push: `git push origin feature/my-feature`
4. Pull Request erstellen

## 📄 Lizenz

[Lizenz hier einfügen]

## 👥 Team

[Team-Info hier einfügen]

---

**Status**: 🚧 In Entwicklung

Letzte Aktualisierung: Oktober 2025

