<img width="1840" height="614" alt="image" src="https://github.com/user-attachments/assets/f5d7a692-f24e-47b1-8334-396b1e686e10" />
# BGB Knowledge Graph Project

A comprehensive AI-powered legal assistant for the German Bürgerliches Gesetzbuch (BGB) with knowledge graph capabilities and multi-model support.

## 🚀 Quick Start

### 🔑 Developer Setup Checklist

**Required for all developers:**
1. ✅ Install dependencies: `pipenv install`
2. ✅ Start infrastructure: `docker-compose up -d && ./setup.sh`
3. ✅ **Get Google API key**: https://makersuite.google.com/app/apikey
4. ✅ **Export API key**: `export GOOGLE_API_KEY="your-api-key-here"`
5. ✅ Choose your model and start coding!

### Main Application (Multi-Model CLI)
```bash
# Install dependencies
pipenv install

# Start services (Solr + Blazegraph)
docker-compose up -d

# IMPORTANT: Load data into services (first time only)
./setup.sh

# Option 1: Use local Qwen model (privacy, no costs)
ollama serve
ollama pull qwen3:14B
pipenv run python bgb_ai_multi.py --model qwen "wenn mein hund eine vase kaputt macht muss ich dann zahlen?"

# Option 2: Use Google Gemini API (cloud, high quality)
export GOOGLE_API_KEY="your-api-key-here"
pipenv run python bgb_ai_multi.py --model gemini "wenn mein hund eine vase kaputt macht muss ich dann zahlen?"
```

### Example Usage

Choose between two AI models based on your needs:

```bash
# LOCAL MODEL (Qwen) - Privacy & No Costs
pipenv run python bgb_ai_multi.py --model qwen "Mein Hund hat eine Vase zerbrochen. Muss ich zahlen?"

# CLOUD MODEL (Gemini) - High Quality & Fast
export GOOGLE_API_KEY="your-api-key-here"
pipenv run python bgb_ai_multi.py --model gemini "Was sind die Statistiken des BGB Knowledge Graphs?"

# Legacy CLI (Qwen only)
pipenv run python bgb_ai_qwen.py "Was sind die zentralen Aspekte eines Kaufvertrages?"
```

## 📁 Project Structure

```
kg_project/
├── bgb_ai_multi.py             # ✅ MAIN MULTI-MODEL CLI (USE THIS)
├── bgb_ai_qwen.py              # 🔧 Legacy Qwen-only CLI (for compatibility)
├── langchain_service/          # ✅ AI AGENTS & TOOLS
│   ├── qwen_agent_bgb.py       #     Local Qwen-Agent implementation  
│   ├── gemini_agent_bgb.py     #     Cloud Gemini API implementation
│   └── tools.py                #     BGB tools (Solr, SPARQL)
├── blazegraph_instance/        # 📊 SPARQL DATABASE
│   ├── load_blazegraph.py      #     Data loading utilities
│   └── query_sparql.py         #     SPARQL query interface
├── kg_search_index/            # 🔍 SOLR SEARCH
│   ├── build_solr_index.py     #     Index building utilities
│   ├── configure_solr.py       #     Solr configuration
│   └── query_bgb.py            #     Search interface
├── kg_curation/                # 🏗️ DATA TRANSFORMATION
│   ├── build_graph.py          #     RDF graph generation
│   ├── model.py                #     Data models & ontology
│   └── transform_raw_data.py   #     XML to structured data
├── AI_MODELS.md                # 📖 Model comparison and setup guide
└── docker-compose.yml          # 🐳 INFRASTRUCTURE SETUP
```

## 🎯 Features

- ✅ **Multi-Model Support** - Choose between local Qwen (privacy) or cloud Gemini (performance)
- ✅ **Native Function Calling** - Uses qwen3:14B and Gemini with official frameworks
- ✅ **Real-time Tool Execution** - Direct integration with Solr and SPARQL endpoints  
- ✅ **Thinking Mode** - Reasoning traces show the AI's decision process (Qwen only)
- ✅ **German Legal Analysis** - Context-aware responses based on actual BGB knowledge graph
- ✅ **Production Ready** - Clean error handling and robust conversation management

## 🧠 AI Architecture

### Multi-Model Support

**Local Model (Qwen)**: 
- Privacy-focused, runs completely offline
- Requires Ollama with qwen3:14B model
- Includes thinking mode for reasoning traces
- No API costs

**Cloud Model (Gemini)**:
- High-quality responses via Google API
- Fast processing, no local compute needed
- Requires GOOGLE_API_KEY environment variable
- Pay-per-use pricing

### Core Components

1. **Multi-Model CLI** (`bgb_ai_multi.py`)
   - Model selection: `--model qwen` or `--model gemini`
   - Unified interface for both models
   - Automatic error handling and fallbacks

2. **AI Agents**
   - `qwen_agent_bgb.py`: Local Qwen-Agent framework integration
   - `gemini_agent_bgb.py`: Cloud Google Generative AI integration
   - Both use identical tools and produce comparable results

3. **Legal Tools** (`langchain_service/tools.py`)
   - `bgb_solr_search`: Full-text search across BGB articles (limit: 5 results)
   - `execute_bgb_sparql_query`: Dynamic SPARQL queries for deep legal analysis
   - Integrated with real Solr and Blazegraph endpoints

3. **Knowledge Graph Infrastructure**
   - **Solr Search Index**: 4,200+ BGB documents with full-text search
   - **Blazegraph SPARQL Database**: 19,071+ triples with structured legal relationships
   - **Custom BGB Ontology**: Legal concepts, norms, paragraphs, and relationships

### Workflow
1. **User asks question** in German 🇩🇪
2. **Agent searches** Solr index for relevant BGB articles 🔍
3. **Agent explores** entities via SPARQL for detailed analysis 🔎
4. **Agent synthesizes** comprehensive legal response 📝

## 🏗️ Infrastructure Components

### Blazegraph SPARQL Database
- **Purpose**: Structured queries and knowledge graph exploration
- **Content**: 19,071 triples covering complete BGB
- **Capabilities**: Complex legal relationship queries, entity exploration
- **Endpoint**: http://localhost:9999/bigdata/sparql

### Solr Search Index  
- **Purpose**: Fast full-text search across BGB content
- **Content**: 4,200+ indexed documents with legal concepts
- **Capabilities**: Natural language search, relevance scoring
- **Endpoint**: http://localhost:8984/solr/bgb_core

### Knowledge Graph Statistics
- **Total Triples**: 19,071
- **Legal Concepts**: 466
- **Norms**: 16  
- **Paragraphs**: 3,759
- **Coverage**: Complete BGB (Books 1-5)
- **Performance**: < 200ms average query time

## 🔧 Development Setup

### Prerequisites
- Python 3.11+ with pipenv
- Docker (for Solr + Blazegraph)
- **For Local Model**: Ollama with qwen3:14B model
- **For Cloud Model**: Google API key (get from https://makersuite.google.com/app/apikey)

### Installation
```bash
# Clone and install
git clone <repo>
cd kg_project
pipenv install

# Start infrastructure
docker-compose up -d

# Setup for Local Model (Qwen)
ollama serve
ollama pull qwen3:14B

# Setup for Cloud Model (Gemini) - REQUIRED FOR DEVELOPERS
export GOOGLE_API_KEY="your-api-key-here"
# Or add to .env file for permanent setup
echo "GOOGLE_API_KEY=your-api-key-here" >> .env
```

### 🔑 Important for Developers - API Key Setup

**All developers must export their Google API key to use Gemini functionality:**

1. **Get your free API key**: https://makersuite.google.com/app/apikey
2. **Export the key**: `export GOOGLE_API_KEY="your-api-key-here"`
3. **Test setup**: `pipenv run python bgb_ai_multi.py --model gemini "Test"`

Without the API key, only the local Qwen model will be available.

### Complete Setup (First Time)
```bash
# 1. Build the knowledge graph from XML data in git is the ttl so not needed most of the time
pipenv run python kg_curation/transform_raw_data.py --input kg_curation/data/BJNR001950896.xml --output kg_curation/output/bgb.json --jsonld
pipenv run python kg_curation/build_graph.py --input kg_curation/output/bgb.json --output kg_curation/output/bgb.ttl

# 2. Run automated setup script (loads data into Solr + Blazegraph)
./setup.sh

# 3. Test the application
pipenv run python bgb_ai_multi.py --model qwen "Test question"
# OR (if you have Gemini API key)
pipenv run python bgb_ai_multi.py --model gemini "Test question"
```

### Manual Setup Steps (Alternative to setup.sh)
1. **Build Knowledge Graph**: Use `kg_curation/` scripts to transform XML data to RDF
2. **Start Services**: Run `docker-compose up -d` for Solr and Blazegraph
3. **Configure Solr**: Run `kg_search_index/configure_solr.py` to set up schema
4. **Index for Search**: Run `kg_search_index/build_solr_index.py` to create Solr index  
5. **Load into Blazegraph**: Use `blazegraph_instance/load_blazegraph.py` to populate SPARQL database
6. **Start AI Assistant**: Run `bgb_ai_multi.py` for interactive legal analysis with model choice

### Services
- **Solr Admin UI**: http://localhost:8984/solr/#/bgb_core
- **Blazegraph Workbench**: http://localhost:9999/blazegraph
- **Ollama API**: http://localhost:11434

### Important Notes
- **First-time setup**: Use `./setup.sh` script to automatically load BGB data into both Solr and Blazegraph
- **Data Requirements**: The setup requires `kg_curation/output/bgb.ttl` file (generated from XML data)
- **Service Dependencies**: Both Solr and Blazegraph must be populated with data before the AI assistant can function properly

## 📊 Example Legal Questions

### General Legal Concepts
- "Was ist ein Kaufvertrag nach BGB?"
- "Welche Rechte haben Mieter bei Mängeln?"
- "Wann ist ein Vertrag nichtig?"

### Specific Legal Scenarios  
- "Mein Hund hat fremdes Eigentum beschädigt. Bin ich haftbar?"
- "Kann ich einen Kaufvertrag widerrufen?"
- "Was passiert bei Verzug des Schuldners?"

### Knowledge Graph Analysis
- "Was sind die Statistiken des BGB Knowledge Graphs?"
- "Zeige mir die Beziehungen zwischen § 433 und anderen Normen"
- "Welche rechtlichen Konzepte sind im Graph definiert?"
- "Wie viele Normen sind in Book 2 des BGB enthalten?"

---

**Built with:** Python, LangChain, Qwen-Agent, Google Generative AI, Solr, Blazegraph, Docker
