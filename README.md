# Prompter - AI Visibility Platform

Production-ready SaaS platform that helps brands get discovered by AI assistants (ChatGPT, Claude, Gemini, Perplexity) by creating & hosting AI-friendly pages and measuring before/after visibility.

## 🏗️ Architecture

This is a monorepo containing:

- **apps/web**: Next.js 14 frontend (App Router, React, TypeScript, Tailwind, shadcn/ui)
- **apps/api**: FastAPI backend (Python 3.11, SQLAlchemy, Alembic)
- **apps/worker**: Background worker for scans and async jobs (RQ)
- **packages/ui**: Shared UI components
- **packages/types**: Shared TypeScript types
- **infra**: Docker, Terraform, Kubernetes manifests

## 🚀 Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- pnpm 8+
- Docker & Docker Compose
- PostgreSQL 15
- Redis 7

### Local Development

1. **Clone and install dependencies**

```bash
git clone <repo>
cd prompter
pnpm install
```

2. **Setup environment**

```bash
cp .env.example .env
# Edit .env with your API keys and config
```

3. **Start infrastructure services**

```bash
docker-compose up -d postgres redis
```

4. **Run database migrations**

```bash
cd apps/api
python -m alembic upgrade head
```

5. **Seed demo data**

```bash
python scripts/seed.py
```

6. **Start development servers**

```bash
# Terminal 1 - API
cd apps/api
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Worker
cd apps/worker
python -m app.main

# Terminal 3 - Web
cd apps/web
pnpm dev
```

Visit http://localhost:3000

### Docker Compose (Recommended)

```bash
docker-compose up --build
```

All services will be available:
- Web: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📊 Core Features

### AI Mention Tracker
- Run scheduled prompts against OpenAI, Anthropic, Google AI
- Extract brand mentions, sentiment, position
- Longitudinal tracking and trends

### Optimization & Hosting
- Generate AI-friendly "Knowledge Pages"
- Fast, structured, schema-rich content
- Host under client subdomains (e.g., acme.prompter.site)

### Analytics Dashboard
- Visibility score and trends
- Competitor comparisons
- Before/after impact analysis
- Page health metrics

### Billing & Auth
- Clerk/Auth0 OIDC authentication
- Role-based access control (Owner/Admin/Member)
- Stripe subscriptions with metered billing
- Plans: Starter, Growth, Enterprise

## 🧪 Testing

```bash
# Backend tests
cd apps/api
pytest --cov=app --cov-report=html

# Frontend tests
cd apps/web
pnpm test

# E2E tests
cd apps/web
pnpm test:e2e
```

## 🔒 Security

- OWASP Top 10 protections
- CSRF tokens for SSR routes
- Strict CORS policy
- Rate limiting on all endpoints
- PII minimization
- Row-level security per tenant
- Secrets via environment variables
- Dependency scanning (pip-audit, npm audit)

## 📦 Deployment

### Production Stack

- **Web**: Vercel or Fly.io
- **Database**: Neon, Supabase, or AWS RDS
- **Redis**: Upstash or Redis Cloud
- **Storage**: AWS S3 or compatible
- **CDN**: Cloudflare
- **Monitoring**: Grafana Cloud, Datadog, Sentry

### Deploy with Fly.io

```bash
# Deploy API
cd apps/api
flyctl deploy

# Deploy Worker
cd apps/worker
flyctl deploy
```

### Deploy Web to Vercel

```bash
cd apps/web
vercel deploy --prod
```

## 🛠️ Tech Stack

### Frontend
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts
- React Hook Form + Zod

### Backend
- FastAPI
- SQLAlchemy + Alembic
- Pydantic v2
- Redis Queue (RQ)
- Boto3 (S3)

### Infrastructure
- PostgreSQL 15 + pgvector
- Redis 7
- Docker
- Terraform
- Kubernetes (optional)

### Integrations
- Clerk (Auth)
- Stripe (Billing)
- OpenAI API
- Anthropic Claude API
- Google Gemini API
- Postmark (Email)
- OpenTelemetry (Observability)
- Sentry (Error Tracking)

## 📁 Project Structure

```
prompter/
├── apps/
│   ├── web/              # Next.js frontend
│   ├── api/              # FastAPI backend
│   └── worker/           # Python worker
├── packages/
│   ├── ui/               # Shared UI components
│   └── types/            # Shared types
├── infra/
│   ├── docker/           # Dockerfiles
│   ├── k8s/              # Kubernetes manifests
│   └── terraform/        # IaC
├── scripts/              # Setup & seed scripts
├── docs/                 # Documentation
└── .github/workflows/    # CI/CD
```

## 🔑 Environment Variables

See `.env.example` for all required environment variables.

## 📖 Documentation

- [Architecture](docs/architecture.md)
- [Data Model](docs/data-model.md)
- [API Reference](docs/api-reference.md)
- [Security Model](docs/security.md)
- [Billing & Limits](docs/billing.md)
- [Deployment Guide](docs/deployment.md)

## 📄 License

MIT License - see LICENSE file for details

