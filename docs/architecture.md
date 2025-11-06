# Architecture

## Overview

Prompter is a production-ready SaaS platform built as a monorepo with three main services:

- **Web**: Next.js 14 frontend with App Router
- **API**: FastAPI backend with SQLAlchemy
- **Worker**: Python background worker using Redis Queue

## System Architecture

```
┌─────────────┐
│   Cloudflare│
│     CDN     │
└──────┬──────┘
       │
       ├─────────────┐
       │             │
┌──────▼──────┐  ┌──▼──────────┐
│   Next.js   │  │  Knowledge  │
│     Web     │  │    Pages    │
│  (Vercel)   │  │  (Subdomain)│
└──────┬──────┘  └─────────────┘
       │
       │ API Calls
       │
┌──────▼──────┐
│   FastAPI   │◄────────┐
│     API     │         │
│  (Fly.io)   │         │
└──────┬──────┘         │
       │                │
       ├────────┐       │
       │        │       │
┌──────▼──┐ ┌──▼───────▼──┐
│PostgreSQL│ │    Redis    │
│  +pgvector│ │   Queue     │
└──────────┘ └──────┬──────┘
                    │
              ┌─────▼─────┐
              │  Worker   │
              │  (Fly.io) │
              └───────────┘
```

## Data Flow

### Scan Execution Flow

1. User creates scan run via Web UI
2. API creates `ScanRun` record with `QUEUED` status
3. Job queued to Redis
4. Worker picks up job:
   - Fetches prompts from database
   - Calls LLM providers (OpenAI, Anthropic, Google)
   - Extracts mentions using `MentionExtractor`
   - Saves results to database
   - Updates scan status to `DONE`
5. User views results in Web UI

### Page Generation Flow

1. User creates knowledge page via Web UI
2. API creates `KnowledgePage` record in `DRAFT` status
3. Job queued to Redis
4. Worker picks up job:
   - Crawls specified URLs
   - Generates content using GPT-4
   - Creates JSON-LD schema
   - Calculates page health score
   - Saves to database
5. User reviews and publishes page
6. Page served at subdomain (e.g., `acme.prompter.site`)

## Tech Stack

### Frontend
- **Framework**: Next.js 14 with App Router
- **UI**: shadcn/ui + Tailwind CSS
- **Auth**: Clerk
- **State**: TanStack Query
- **Forms**: React Hook Form + Zod

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy + Alembic
- **Auth**: JWT (RS256) via Clerk
- **Queue**: Redis Queue (RQ)
- **Storage**: S3-compatible

### Infrastructure
- **Database**: PostgreSQL 15 + pgvector
- **Cache/Queue**: Redis 7
- **Hosting**: Vercel (Web), Fly.io (API/Worker)
- **CDN**: Cloudflare
- **Monitoring**: OpenTelemetry, Sentry

### Integrations
- **LLMs**: OpenAI, Anthropic, Google
- **Payments**: Stripe
- **Email**: Postmark

## Security

### Authentication & Authorization
- OIDC/JWT via Clerk
- Row-level security (org-scoped queries)
- Role-based access control (Owner/Admin/Member)

### API Security
- CORS with whitelist
- Rate limiting (60 req/min default)
- Request size limits
- CSRF protection on SSR routes
- Security headers (Helmet)

### Data Security
- Secrets via environment variables
- PII minimization
- Audit logging for sensitive actions
- API keys hashed in database

### Network Security
- TLS/HTTPS only
- Trusted host middleware
- DNS security (DNSSEC on Cloudflare)

## Scalability

### Horizontal Scaling
- API: Scale Fly.io instances
- Worker: Scale worker processes
- Web: Vercel auto-scales

### Database
- Connection pooling (10 connections per API instance)
- Read replicas for analytics queries
- Indexes on frequently queried columns

### Caching
- Redis for session data
- API response caching (TanStack Query)
- CDN caching for static assets

### Rate Limiting
- Per-org limits enforced at API level
- LLM provider rate limiting with backoff
- Circuit breaker pattern for external APIs

## Monitoring & Observability

### Metrics
- OpenTelemetry for distributed tracing
- Custom business metrics (visibility score, etc.)
- Infrastructure metrics (CPU, memory, latency)

### Logging
- Structured logging with log levels
- Request/response logging
- Error tracking with Sentry

### Alerts
- API error rate threshold
- Database connection pool exhaustion
- Worker queue depth
- Scan failure rate

## Deployment

### Environments
- **Development**: Local with Docker Compose
- **Staging**: Fly.io + Neon DB
- **Production**: Fly.io + managed DB + Cloudflare

### CI/CD Pipeline
1. Lint & test on PR
2. Build Docker images
3. Deploy to staging on merge to `develop`
4. Deploy to production on merge to `main`
5. Run migrations
6. Invalidate CDN cache

### Rollback Strategy
- Blue/green deployment on Fly.io
- Database migration rollback scripts
- Feature flags for gradual rollout

## Performance

### Target Metrics
- API response time: < 200ms (p95)
- Page load time: < 2s (LCP)
- Scan execution time: < 5 min for 10 prompts x 3 models
- Database query time: < 50ms (p95)

### Optimizations
- Database indexes on foreign keys
- Eager loading for relationships
- Background jobs for heavy operations
- CDN for static assets
- Image optimization

## Disaster Recovery

### Backups
- PostgreSQL: Daily backups, 30-day retention
- Redis: Persistence enabled (AOF)
- S3: Versioning enabled

### Recovery Plan
1. Restore database from backup
2. Redeploy services from Git
3. Re-run migrations if needed
4. Verify data integrity
5. Resume operations

### RTO/RPO
- **RTO** (Recovery Time Objective): < 1 hour
- **RPO** (Recovery Point Objective): < 24 hours

