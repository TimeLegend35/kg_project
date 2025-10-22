<img width="1840" height="614" alt="image" src="https://github.com/user-attachments/assets/f5d7a692-f24e-47b1-8334-396b1e686e10" />
# BGB Knowledge Graph Project

A comprehensive AI-powered legal assistant for the German Bürgerliches Gesetzbuch (BGB) with knowledge graph capabilities.

## 🚀 Quick Start

### Main Application (Recommended)
```bash
# Install dependencies
pipenv install

# Start services (Solr + Blazegraph)
docker-compose up -d

# IMPORTANT: Load data into services (first time only)
./setup.sh

# Start Ollama with Qwen model
ollama serve
ollama pull qwen3:14B

# Run the BGB AI Assistant
pipenv run python bgb_ai_qwen.py "wenn mein hund eine vase kaputt macht muss ich dann zahlen?"
```

### Example Usage
```bash
# Ask about dog liability
pipenv run python bgb_ai_qwen.py "Mein Hund hat eine Vase zerbrochen. Muss ich zahlen?"

# Get knowledge graph statistics via SPARQL queries
pipenv run python bgb_ai_qwen.py "Was sind die Statistiken des BGB Knowledge Graphs?"

# Ask about contracts
pipenv run python bgb_ai_qwen.py "Was sind die zentralen Aspekte eines Kaufvertrages?"
```

## 📁 Project Structure

```
kg_project/
├── bgb_ai_qwen.py              # ✅ MAIN CLI APPLICATION
├── langchain_service/          # ✅ AI AGENT & TOOLS
│   ├── qwen_agent_bgb.py       #     Core Qwen-Agent implementation  
│   └── tools.py                #     BGB tools (Solr, SPARQL)
├── blazegraph_instance/        # 📊 SPARQL DATABASE
│   ├── load_blazegraph.py      #     Data loading utilities
│   └── query_sparql.py         #     SPARQL query interface
├── kg_search_index/            # 🔍 SOLR SEARCH
│   ├── build_solr_index.py     #     Index building utilities
│   ├── configure_solr.py       #     Solr configuration
│   ├── query_bgb.py            #     Search interface
│   └── README.md               #     Solr setup documentation
├── kg_curation/                # 🏗️ DATA TRANSFORMATION
│   ├── build_graph.py          #     RDF graph generation
│   ├── model.py                #     Data models & ontology
│   └── transform_raw_data.py   #     XML to structured data
└── docker-compose.yml          # 🐳 INFRASTRUCTURE SETUP
```

## 🎯 Features

- ✅ **Native Qwen Function Calling** - Uses qwen3:14B model with official Qwen-Agent framework
- ✅ **Real-time Tool Execution** - Direct integration with Solr and SPARQL endpoints  
- ✅ **Thinking Mode** - Reasoning traces show the AI's decision process
- ✅ **German Legal Analysis** - Context-aware responses based on actual BGB knowledge graph
- ✅ **Production Ready** - Clean error handling and robust conversation management

## 🧠 AI Architecture

### Core Components

1. **AI Agent** (`langchain_service/qwen_agent_bgb.py`)
   - Qwen-Agent framework integration
   - Native function calling support
   - Streaming responses with thinking mode

2. **Legal Tools** (`langchain_service/tools.py`)
   - `bgb_solr_search`: Full-text search across BGB articles
   - `explore_bgb_entity_with_sparql`: Deep legal analysis via SPARQL
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
- Ollama with qwen3:14B model
- qwen-agent framework

### Installation
```bash
# Clone and install
git clone <repo>
cd kg_project
pipenv install

# Start infrastructure
docker-compose up -d

# Setup Ollama
ollama serve
ollama pull qwen3:14B
```

### Complete Setup (First Time)
```bash
# 1. Build the knowledge graph from XML data in git is the ttl so not needed most of the time
pipenv run python kg_curation/transform_raw_data.py --input kg_curation/data/BJNR001950896.xml --output kg_curation/output/bgb.json --jsonld
pipenv run python kg_curation/build_graph.py --input kg_curation/output/bgb.json --output kg_curation/output/bgb.ttl

# 2. Run automated setup script (loads data into Solr + Blazegraph)
./setup.sh

# 3. Test the application
pipenv run python bgb_ai_qwen.py "Test question"
```

### Manual Setup Steps (Alternative to setup.sh)
1. **Build Knowledge Graph**: Use `kg_curation/` scripts to transform XML data to RDF
2. **Start Services**: Run `docker-compose up -d` for Solr and Blazegraph
3. **Configure Solr**: Run `kg_search_index/configure_solr.py` to set up schema
4. **Index for Search**: Run `kg_search_index/build_solr_index.py` to create Solr index  
5. **Load into Blazegraph**: Use `blazegraph_instance/load_blazegraph.py` to populate SPARQL database
6. **Start AI Assistant**: Run `bgb_ai_qwen.py` for interactive legal analysis

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

**Built with:** Python, LangChain, Qwen-Agent, Solr, Blazegraph, Docker
