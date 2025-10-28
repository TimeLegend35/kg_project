#!/bin/bash
# Quick start script for BGB AI Chat API

echo "🚀 Starting BGB AI Chat API..."
echo "================================"

# Check if .env exists, if not copy from example
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
fi

# Start services
echo "🐳 Starting Docker services (PostgreSQL + API)..."
docker-compose up -d postgres

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Run migrations
echo "🔄 Running database migrations..."
docker-compose run --rm api alembic upgrade head

# Start API
echo "🚀 Starting API service..."
docker-compose up -d api

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📡 API available at: http://localhost:8080"
echo "📚 Documentation at: http://localhost:8080/docs"
echo "🏥 Health check: http://localhost:8080/healthz"
echo ""
echo "🔑 API Key (for testing): dev-api-key-change-me"
echo ""
echo "📋 Useful commands:"
echo "  docker-compose logs -f api     # View API logs"
echo "  docker-compose ps              # Check service status"
echo "  docker-compose down            # Stop all services"
echo ""
echo "🧪 Test the API:"
echo '  curl http://localhost:8080/healthz'
echo '  curl -H "X-API-Key: dev-api-key-change-me" http://localhost:8080/api/v1/agents'

