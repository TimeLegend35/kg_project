#!/bin/bash

echo "🚀 Starting BGB Chat Service"
echo "============================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env not found! Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env created"
    echo ""
fi

# Start API
echo "🔄 Starting FastAPI server..."
echo "📚 API Docs: http://localhost:8000/docs"
echo "🏥 Health: http://localhost:8000/health"
echo ""

python -m uvicorn chat_api.main:app --reload --host 0.0.0.0 --port 8000

