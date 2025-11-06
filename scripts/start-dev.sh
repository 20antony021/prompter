#!/bin/bash

echo "🚀 Starting Prompter in development mode..."
echo ""
echo "⚠️  Note: This requires PostgreSQL and Redis to be running locally"
echo "   - PostgreSQL on localhost:5432"
echo "   - Redis on localhost:6379"
echo ""
echo "   Or start with Docker: docker-compose up -d postgres redis"
echo ""

# Check if we're in the right directory
cd /Users/antonydubost/prompter

# Export environment variables
export DATABASE_URL="postgresql://prompter:password@localhost:5432/prompter"
export REDIS_URL="redis://localhost:6379/0"
export OPENAI_API_KEY="sk-demo-key"
export ANTHROPIC_API_KEY="sk-ant-demo-key"
export GOOGLE_GENAI_API_KEY="demo-key"
export CLERK_SECRET_KEY="sk_test_demo"
export CLERK_JWKS_URL="https://demo.clerk.accounts.dev/.well-known/jwks.json"
export STRIPE_SECRET_KEY="sk_test_demo"
export STRIPE_WEBHOOK_SECRET="whsec_demo"
export LOG_LEVEL="INFO"

echo "Starting Next.js development server on http://localhost:3000..."
echo ""

cd apps/web
pnpm dev

