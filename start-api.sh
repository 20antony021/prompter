#!/bin/bash

# Start API Server Script
# This script starts the FastAPI backend server

set -e

echo "🚀 Starting Prompter API Server"
echo "================================"

# Check if we're in the right directory
if [ ! -f "apps/api/app/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   cd /Users/antonydubost/prompter"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if database is accessible
echo "📊 Checking database connection..."
cd apps/api

# Try to run a simple database check
python3 -c "from app.database import SessionLocal; db = SessionLocal(); db.close(); print('✅ Database connection successful')" 2>/dev/null || {
    echo "⚠️  Warning: Cannot connect to database"
    echo "   Make sure PostgreSQL is running:"
    echo "   docker-compose up -d postgres"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

echo ""
echo "🔥 Starting API server on http://localhost:8000"
echo "📚 API docs will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the API server
uvicorn app.main:app --reload --port 8000

