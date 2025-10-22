# BGB AI Assistant - Multi-Model Support

This project now supports multiple AI models for the BGB (German Civil Code) assistant:

## Available Models

### 1. Local Qwen Model (Default)
- **File**: `qwen_agent_bgb.py`
- **CLI**: `bgb_ai_qwen.py` or `bgb_ai_multi.py --model qwen`
- **Advantages**: 
  - Runs completely locally
  - No API costs
  - Privacy (no data sent to cloud)
  - Thinking mode for reasoning traces
- **Requirements**: 
  - Ollama running locally
  - Qwen model downloaded (`ollama pull qwen3:14B`)

### 2. Google Gemini Model
- **File**: `gemini_agent_bgb.py`
- **CLI**: `bgb_ai_multi.py --model gemini`
- **Advantages**:
  - High-quality responses
  - Fast processing
  - No local compute requirements
- **Requirements**:
  - Google API key (get from https://makersuite.google.com/app/apikey)
  - Internet connection
  - API usage costs apply
  - **DEVELOPERS: Must export GOOGLE_API_KEY environment variable**

## Usage

### Quick Start with Qwen (Local)
```bash
# Using the original CLI
pipenv run python bgb_ai_qwen.py "Mein Hund hat eine Vase zerbrochen. Muss ich zahlen?"

# Using the multi-model CLI
pipenv run python bgb_ai_multi.py --model qwen "Was ist §833 BGB?"
```

### Using Gemini (Cloud) - API Key Required
```bash
# REQUIRED: Set your Google API key (all developers must do this)
export GOOGLE_API_KEY="your-api-key-here"

# Use Gemini model
pipenv run python bgb_ai_multi.py --model gemini "Was sind die Statistiken des BGB?"

# Use specific Gemini model variant  
pipenv run python bgb_ai_multi.py --model gemini --gemini-model gemini-2.5-flash "Schnelle Frage zu §833"
```

## Installation

### Basic Installation
```bash
# Install all dependencies
pipenv install

# For Gemini support specifically
pipenv install google-generativeai
```

### Setup for Qwen (Local)
```bash
# Install and start Ollama
ollama serve

# Download Qwen model
ollama pull qwen3:14B
```

### Setup for Gemini (Cloud) - REQUIRED FOR DEVELOPERS
```bash
# STEP 1: Get API key from: https://makersuite.google.com/app/apikey
# STEP 2: Export your API key (required for all developers)
export GOOGLE_API_KEY="your-api-key-here"

# Alternative: Add to your .env file for permanent setup
echo "GOOGLE_API_KEY=your-api-key-here" >> .env

# STEP 3: Test the setup
pipenv run python bgb_ai_multi.py --model gemini "Test Gemini setup"
```

**⚠️ Important for Developers:**
- **All developers must export their Google API key** to use Gemini functionality
- Get your free API key at: https://makersuite.google.com/app/apikey
- Without the API key, only Qwen (local) model will be available
- Add the key to your shell profile for permanent setup

## Features

Both models support:
- ✅ **Dynamic tool selection**: Automatically chooses between Solr search and SPARQL queries
- ✅ **Real-time function execution**: Executes searches and queries as needed
- ✅ **German language support**: Native German responses and prompts
- ✅ **BGB-specific knowledge**: Optimized for German Civil Code queries
- ✅ **Multi-step reasoning**: Can combine multiple searches and analyses

## Command Options

### Multi-Model CLI (`bgb_ai_multi.py`)
```bash
python bgb_ai_multi.py [OPTIONS] "your question"

Options:
  --model {qwen,gemini}     Choose AI model (default: qwen)
  --gemini-model MODEL      Specific Gemini variant (default: gemini-2.5-flash)
  -h, --help               Show help message
```

### Legacy CLI (`bgb_ai_qwen.py`)
```bash
python bgb_ai_qwen.py "your question"
```

## Architecture

Both agents use the same:
- **Tools**: `bgb_solr_search` and `execute_bgb_sparql_query` from `tools.py`
- **Function conversion**: Dynamic conversion from LangChain tools to model-specific formats
- **Error handling**: German-language error messages, short and context-efficient
- **Services**: Solr (localhost:8984) and Blazegraph (localhost:9999)

## Model Comparison

| Feature | Qwen (Local) | Gemini (Cloud) |
|---------|--------------|----------------|
| **Cost** | Free | Pay per use |
| **Privacy** | Complete | Data sent to Google |
| **Speed** | Depends on hardware | Fast |
| **Quality** | Good | Excellent |
| **Setup** | Ollama required | API key required |
| **Offline** | Yes | No |

## Troubleshooting

### Qwen Issues
- Ensure Ollama is running: `ollama serve`
- Check model is available: `ollama list`
- Verify model name matches in code

### Gemini Issues
- **Check API key is set**: `echo $GOOGLE_API_KEY`
- **Get API key**: https://makersuite.google.com/app/apikey
- Verify internet connection
- Check API quota limits
- **For developers**: API key must be exported in shell environment

### Service Issues
- Solr: `curl http://localhost:8984/solr/bgb_core/admin/ping`
- Blazegraph: `curl http://localhost:9999/bigdata`

Both models will fall back gracefully if services are unavailable.