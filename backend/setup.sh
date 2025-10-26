#!/bin/bash

# BGB Knowledge Graph Search Setup Script
# This script sets up the complete search infrastructure

set -e

echo "🏛️  BGB Knowledge Graph Search Setup"
echo "====================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if TTL file exists
TTL_FILE="kg_curation/output/bgb.ttl"
if [ ! -f "$TTL_FILE" ]; then
    echo "❌ TTL file not found: $TTL_FILE"
    echo "Please run the knowledge graph curation first:"
    echo "  pipenv run python kg_curation/transform_raw_data.py --input kg_curation/data/BJNR001950896.xml --output kg_curation/output/bgb.json --jsonld"
    echo "  pipenv run python kg_curation/build_graph.py --input kg_curation/output/bgb.json --output kg_curation/output/bgb.ttl"
    exit 1
fi

echo "📁 Found TTL file: $TTL_FILE"

# Start Solr container
echo "🚀 Starting BGB Solr and Blazegraph containers..."
docker-compose up -d

# Wait for Solr to be ready
echo "⏳ Waiting for Solr to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:8984/solr/admin/cores > /dev/null 2>&1; then
        echo "✅ Solr is ready!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "❌ Solr failed to start within 60 seconds"
        docker-compose logs
        exit 1
    fi
    sleep 1
done

# Configure Solr schema
echo "⚙️  Configuring Solr schema..."
pipenv run python kg_search_index/configure_solr.py

# Install Python dependencies if not already installed
echo "📦 Checking Python dependencies..."
if ! pipenv run python -c "import requests" > /dev/null 2>&1; then
    echo "Installing dependencies with pipenv..."
    pipenv install
fi

# Build the search index
echo "🔍 Building search index..."
pipenv run python kg_search_index/build_solr_index.py --clear-index --test-search "Ehegatte"

# Load data into Blazegraph
echo "📊 Loading data into Blazegraph..."
pipenv run python blazegraph_instance/load_blazegraph.py --wait --clear-database --test-query "Ehegatte"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Available commands:"
echo "  # Solr (Natural Language Search)"
echo "  pipenv run query \"search terms\"                       # Single query"
echo "  pipenv run query-interactive                            # Interactive mode"
echo "  pipenv run query --type norm \"Eigentum\"                # Type-filtered search"
echo "  pipenv run build-index --clear-index                    # Rebuild index"
echo ""
echo "  # Blazegraph (SPARQL Queries)"
echo "  pipenv run sparql --concepts Ehegatte                   # Search concepts"
echo "  pipenv run sparql --paragraphs Vertrag                  # Search paragraphs"
echo "  pipenv run sparql-interactive                           # Interactive SPARQL"
echo "  pipenv run load-blazegraph --clear-database             # Reload data"
echo ""
echo "Web Interfaces:"
echo "  Solr UI:       http://localhost:8984/solr/#/bgb_core"
echo "  Blazegraph UI: http://localhost:9999/blazegraph"
echo ""
echo "Example queries to try:"
echo "  - Ehegatte (spouse)"
echo "  - Vertrag (contract)"
echo "  - Eigentum (property)"
echo "  - Erbe (inheritance)"