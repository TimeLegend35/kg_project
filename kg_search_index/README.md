# BGB Knowledge Graph Solr Search Index

This module provides a comprehensive search index for the BGB (Bürgerliches Gesetzbuch) knowledge graph using Apache Solr. It enables natural language queries to find specific URI nodes in the knowledge graph.

## Features

- **Full-text search** across all legal concepts, norms, and paragraphs
- **German language support** with proper tokenization and stemming
- **Natural language queries** to find relevant URI nodes
- **Dedicated Solr container** to avoid conflicts with other projects
- **Interactive query interface** for exploration
- **Batch indexing** with progress reporting

## Setup

### 1. Start the Solr Container

The project includes a dedicated Solr container configuration to avoid conflicts with other Solr instances:

```bash
# Start the BGB Solr container (runs on port 8984)
docker-compose -f docker-compose.bgb-solr.yml up -d

# Check if Solr is running
curl http://localhost:8984/solr/bgb_core/admin/ping
```

### 2. Install Python Dependencies

```bash
# Install dependencies using Pipenv
pipenv install
```

### 3. Build the Search Index

```bash
# Quick setup using Pipenv script
pipenv run setup-search

# Or manual indexing
pipenv run build-index --clear-index

# With custom parameters
pipenv run python kg_search_index/build_solr_index.py \
    --ttl-file kg_curation/output/bgb.ttl \
    --solr-url http://localhost:8984/solr/bgb_core \
    --batch-size 100 \
    --clear-index \
    --test-search "Ehegatte"
```

## Usage

### Command Line Queries

```bash
# Simple search
pipenv run query "Ehegatte"

# Search with type filter
pipenv run query --type norm "Eigentum"

# Limit results
pipenv run query --max-results 5 "Vertrag"
```

### Interactive Mode

```bash
# Start interactive query interface
pipenv run query-interactive
```

Interactive commands:
- `help` - Show available commands
- `/type <type> <query>` - Search within document type (legal_concept, norm, paragraph, legal_code)
- `/uri <partial>` - Find URIs containing text
- `quit` - Exit

### Example Queries

```bash
# Find information about spouses
pipenv run query "Ehegatte"

# Find norms about property
pipenv run query --type norm "Eigentum"

# Find paragraphs mentioning contracts
pipenv run query --type paragraph "Vertrag"

# Find legal concepts about inheritance
pipenv run query --type legal_concept "Erbe"
```

## Index Structure

The Solr index contains the following document types:

### Legal Concepts (`legal_concept`)
- URI: `http://example.org/bgb/data/concept_*`
- Fields: `label`, `uri`, `type`
- Example: concepts like "Ehegatte", "Vertrag", "Eigentum"

### Norms (`norm`)
- URI: `http://example.org/bgb/data/norm_*`
- Fields: `norm_number`, `has_paragraph`, `uri`, `type`
- Example: `norm_1357`, `norm_1566`

### Paragraphs (`paragraph`)
- URI: `http://example.org/bgb/data/norm_*_para_*`
- Fields: `text_content`, `norm_number`, `paragraph_number`, `mentions_concept`, `uri`, `type`
- Contains the actual legal text content

### Legal Code (`legal_code`)
- URI: `http://example.org/bgb/data/BGB`
- Fields: `title`, `has_norm`, `uri`, `type`
- The main BGB document

## Search Features

### Full-Text Search
All text content is indexed with German language processing:
- Tokenization for German text
- Stop word removal
- Stemming with GermanLightStemFilter
- Case-insensitive matching

### Concept Extraction
The indexer automatically identifies legal concepts mentioned in paragraph text and creates cross-references.

### Faceted Search
Results can be filtered by:
- Document type (norm, paragraph, legal_concept, legal_code)
- Norm number
- Related concepts

### Highlighting
Search results include highlighted text snippets showing query matches in context.

## Configuration

### Solr Configuration
- **Port**: 8984 (to avoid conflicts)
- **Core**: bgb_core
- **Schema**: German-optimized text processing
- **Container**: bgb-solr

### Index Fields
- `uri` - Full URI of the resource
- `type` - Document type (norm, paragraph, etc.)
- `search_text` - Combined searchable text
- `text_content` - Full text content for paragraphs
- `label` - Labels for concepts
- `norm_number` - Extracted norm numbers
- `mentions_concept` - Related legal concepts

## Maintenance

### Rebuilding the Index

```bash
# Clear and rebuild the entire index
pipenv run build-index --clear-index

# Add new documents without clearing
pipenv run build-index
```

### Monitoring

```bash
# Check Solr status
curl http://localhost:8984/solr/bgb_core/admin/ping

# View index statistics
curl "http://localhost:8984/solr/bgb_core/admin/luke?wt=json"

# Check document count
curl "http://localhost:8984/solr/bgb_core/select?q=*:*&rows=0&wt=json"
```

### Stopping Solr

```bash
# Stop the BGB Solr container
docker-compose -f docker-compose.bgb-solr.yml down

# Remove volumes (deletes index data)
docker-compose -f docker-compose.bgb-solr.yml down -v
```

## Troubleshooting

### Common Issues

1. **Connection refused**
   ```bash
   # Check if Solr container is running
   docker ps | grep bgb-solr
   
   # Check logs
   docker-compose -f docker-compose.bgb-solr.yml logs
   ```

2. **Index not found**
   ```bash
   # Recreate the core
   docker-compose -f docker-compose.bgb-solr.yml down
   docker-compose -f docker-compose.bgb-solr.yml up -d
   ```

3. **Memory issues**
   ```bash
   # Reduce batch size
   pipenv run build-index --batch-size 50
   ```

### Performance Tips

- Use smaller batch sizes for large datasets
- Filter queries by document type when possible
- Use specific terms rather than very broad queries
- Monitor Solr memory usage during indexing

## API Integration

The query interface can be easily integrated into other applications:

```python
from kg_search_index.query_bgb import BGBQueryInterface

# Create interface
bgb = BGBQueryInterface("http://localhost:8984/solr/bgb_core")

# Search for content
results = bgb.search("Ehegatte", max_results=5)

# Get URIs from results
uris = [doc['uri'] for doc in results]
```