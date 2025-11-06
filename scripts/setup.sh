#!/bin/bash

set -e

echo "🚀 Setting up Prompter development environment..."

# Check prerequisites
echo "Checking prerequisites..."

command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "❌ pnpm is required but not installed. Run: npm install -g pnpm"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }

echo "✅ Prerequisites check passed"

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys"
else
    echo "✅ .env file already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
pnpm install

# Start infrastructure services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres redis

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker-compose exec -T postgres pg_isready -U prompter > /dev/null 2>&1; do
    sleep 1
done

echo "✅ PostgreSQL is ready"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd apps/api
pip install -r requirements.txt
cd ../..

# Run database migrations
echo "🗄️  Running database migrations..."
cd apps/api
python -m alembic upgrade head
cd ../..

# Seed database
echo "🌱 Seeding database with demo data..."
python scripts/seed.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development servers:"
echo ""
echo "  Terminal 1: cd apps/api && uvicorn app.main:app --reload --port 8000"
echo "  Terminal 2: cd apps/worker && python -m app.main"
echo "  Terminal 3: cd apps/web && pnpm dev"
echo ""
echo "Or use: docker-compose up"
echo ""
echo "📖 Documentation: ./docs"
echo "🌐 Web: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Demo account:"
echo "  Email: demo@prompter.site"
echo "  (Setup authentication via Clerk dashboard)"

