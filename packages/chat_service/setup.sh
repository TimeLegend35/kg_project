#!/bin/bash

echo "🚀 BGB Chat Service Setup"
echo "========================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check Prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites OK${NC}"
echo ""

# 2. Navigate to chat service directory
cd packages/chat_service || exit 1

# 3. Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✅ .env created${NC}"
    echo -e "${YELLOW}⚠️  Please review .env and adjust settings if needed${NC}"
else
    echo -e "${GREEN}✅ .env already exists${NC}"
fi
echo ""

# 4. Install Dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# 5. Go back to root and start Docker Services
cd ../..
echo "🐳 Starting Docker services..."
docker-compose up -d bgb-postgres

# 6. Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check if PostgreSQL is ready
if docker exec bgb-postgres pg_isready -U bgb_user -d bgb_chat &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL not ready${NC}"
    exit 1
fi
echo ""

# 7. Initialize Database Tables (wird automatisch beim ersten Start gemacht)
echo "🗄️  Database tables will be created automatically on first API start"
echo ""

# 8. Show summary
echo "="
echo -e "${GREEN}✅ Setup completed!${NC}"
echo "="
echo ""
echo "📚 Next steps:"
echo "  1. Review .env: packages/chat_service/.env"
echo "  2. Start all services: docker-compose up -d"
echo "  3. Start Chat API:"
echo "     cd packages/chat_service"
echo "     python -m uvicorn chat_api.main:app --reload --port 8000"
echo ""
echo "  4. Open API docs: http://localhost:8000/docs"
echo "  5. Test chat:"
echo "     curl -X POST http://localhost:8000/sessions"
echo ""
echo "🔧 Useful commands:"
echo "  - Health check: curl http://localhost:8000/health/detailed"
echo "  - View logs: docker-compose logs -f bgb-postgres"
echo "  - Stop services: docker-compose down"
echo ""

