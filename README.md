# BGB Knowledge Graph Project

A comprehensive AI-powered legal assistant for the German Bürgerliches Gesetzbuch (BGB) with knowledge graph capabilities and multi-model support.

<img width="1840" height="614" alt="BGB Knowledge Graph Interface" src="https://github.com/user-attachments/assets/f5d7a692-f24e-47b1-8334-396b1e686e10" />

## 🚀 Quick Start

### 🔑 Developer Setup (Required)

```bash
# 1. Install dependencies
pipenv install

# 2. Start infrastructure & load data
docker-compose up -d && ./setup.sh

# 3. Get Google API key (required for Gemini model)
# Visit: https://makersuite.google.com/app/apikey
export GOOGLE_API_KEY="your-api-key-here"

# 4. Choose your AI model and start!
```

### Usage Examples

```bash
# Local Model (Qwen) - Privacy-focused, no costs
ollama serve && ollama pull qwen3:14B
pipenv run python bgb_ai_multi.py --model qwen "Mein Hund hat eine Vase zerbrochen. Muss ich zahlen?"

# Cloud Model (Gemini) - High quality, fast
pipenv run python bgb_ai_multi.py --model gemini "Was sind die Rechte von Ehegatten?"
```

## 🎯 Features

- **🤖 Multi-Model AI**: Local Qwen (privacy) or Cloud Gemini (performance)
- **⚖️ Legal Analysis**: Context-aware responses from real BGB knowledge graph
- **🔍 Smart Search**: 7,472 BGB documents with full-text search
- **📊 Knowledge Graph**: 34,511 triples with legal relationships
- **🇩🇪 German Legal Focus**: Native understanding of German civil law
- **🛠️ Function Calling**: Real-time integration with Solr and SPARQL

## 📁 Project Structure

```
kg_project/
├── bgb_ai_multi.py             # ✅ MAIN CLI - Multi-model interface
├── langchain_service/          # 🤖 AI agents & legal tools
│   ├── qwen_agent_bgb.py       #     Local Qwen integration  
│   ├── gemini_agent_bgb.py     #     Cloud Gemini integration
│   └── tools.py                #     BGB search & SPARQL tools
├── kg_search_index/            # 🔍 Solr search (7,472 documents)
├── blazegraph_instance/        # 📊 SPARQL database (34,511 triples)
├── kg_curation/                # 🏗️ Data transformation (XML→RDF)
└── docker-compose.yml          # 🐳 Infrastructure setup
```

## 🧠 AI Architecture

### Model Options

| Model | Privacy | Cost | Quality | Setup |
|-------|---------|------|---------|-------|
| **Qwen (Local)** | ✅ Offline | ✅ Free | ⭐⭐⭐ | Ollama required |
| **Gemini (Cloud)** | ⚠️ Online | 💰 Pay-per-use | ⭐⭐⭐⭐⭐ | API key required |

### Legal Tools
- **BGB Search**: Full-text search across all BGB articles (limit: 5 results)
- **SPARQL Queries**: Dynamic exploration of legal relationships and concepts
- **German Analysis**: Native German language processing for legal contexts

### Infrastructure
- **Solr**: Fast text search (http://localhost:8984/solr)
- **Blazegraph**: Knowledge graph queries (http://localhost:9999/blazegraph)
- **Docker**: Containerized services for easy deployment

## 🔧 Development Setup

### Prerequisites
- Python 3.11+ with pipenv
- Docker (for Solr + Blazegraph)
- **For Qwen**: Ollama with qwen3:14B model
- **For Gemini**: Google API key ([get here](https://makersuite.google.com/app/apikey))

### Complete Installation
```bash
# 1. Clone and install
git clone <repo> && cd kg_project
pipenv install

# 2. Start services and load BGB data
docker-compose up -d
./setup.sh  # Loads 34,511 triples + indexes 7,472 documents

# 3. Setup AI models
# For local model:
ollama serve && ollama pull qwen3:14B

# For cloud model (required for all developers):
export GOOGLE_API_KEY="your-api-key-here"

# 4. Test the system
pipenv run python bgb_ai_multi.py --model qwen "Test question"
```

## 🧪 Testing & Validation

### Fresh Setup Validation
```bash
# Complete cleanup
docker-compose down -v && docker rmi solr:9.4 lyrasis/blazegraph:2.1.5

# Fresh installation
./setup.sh

# Verify functionality
curl http://localhost:8984/solr/bgb_core/admin/ping | jq '.status'  # Should return "OK"
pipenv run python kg_search_index/query_bgb.py "Ehegatte"           # Should find 348 results
pipenv run python bgb_ai_multi.py --model qwen "Test"               # Should get AI response
```

## 📊 Knowledge Graph Statistics

- **Total Triples**: 34,511
- **Indexed Documents**: 7,472
- **Legal Concepts**: 466+
- **BGB Coverage**: Complete (Books 1-5)
- **Search Performance**: <200ms average
- **Languages**: German (native), with English interface

## 📋 Example Legal Questions

### Practical Scenarios
- "Mein Hund hat fremdes Eigentum beschädigt. Bin ich haftbar?"
- "Kann ich einen Kaufvertrag widerrufen?"
- "Was passiert bei Verzug des Schuldners?"

### Legal Concepts
- "Was ist ein Kaufvertrag nach BGB?"
- "Welche Rechte haben Mieter bei Mängeln?"
- "Was sind die Rechte von Ehegatten?"

### Knowledge Graph Analysis
- "Was sind die Statistiken des BGB Knowledge Graphs?"
- "Zeige mir die Beziehungen zwischen § 433 und anderen Normen"

---

**Tech Stack:** Python | Qwen-Agent | Google Generative AI | Solr | Blazegraph | Docker
