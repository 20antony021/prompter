# Deployment Guide

## Prerequisites

- Fly.io account
- Vercel account
- Stripe account
- Clerk account
- OpenAI, Anthropic, and Google AI API keys
- Cloudflare account
- Database (Neon, Supabase, or RDS)
- Redis (Upstash or Redis Cloud)

## Environment Setup

### 1. Database Setup

**Option A: Neon (Recommended)**

```bash
# Create account at neon.tech
# Create database: prompter
# Copy connection string
```

**Option B: Supabase**

```bash
# Create project at supabase.com
# Get PostgreSQL connection string
```

### 2. Redis Setup

```bash
# Create Redis instance at upstash.com
# Copy REDIS_URL
```

### 3. Clerk Setup

```bash
# Create application at clerk.com
# Get publishable and secret keys
# Configure JWT template (RS256)
```

### 4. Stripe Setup

```bash
# Create products and prices in Stripe Dashboard
# Create webhook endpoint
# Copy API keys
```

## Deployment Steps

### 1. Deploy Database Migrations

```bash
cd apps/api

# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://..."

# Run migrations
python -m alembic upgrade head

# Seed initial data
cd ../..
python scripts/seed.py
```

### 2. Deploy API to Fly.io

```bash
cd apps/api

# Create Fly.io app
flyctl apps create prompter-api

# Set secrets
flyctl secrets set \
  DATABASE_URL="postgresql://..." \
  REDIS_URL="redis://..." \
  OPENAI_API_KEY="..." \
  ANTHROPIC_API_KEY="..." \
  GOOGLE_GENAI_API_KEY="..." \
  STRIPE_SECRET_KEY="..." \
  STRIPE_WEBHOOK_SECRET="..." \
  CLERK_SECRET_KEY="..." \
  CLERK_JWKS_URL="..." \
  S3_ENDPOINT="..." \
  S3_BUCKET="..." \
  S3_ACCESS_KEY="..." \
  S3_SECRET_KEY="..." \
  CORS_ORIGINS="https://prompter.site"

# Deploy
flyctl deploy

# Scale
flyctl scale count 2 --region iad
```

Create `fly.toml`:

```toml
app = "prompter-api"
primary_region = "iad"

[build]
  dockerfile = "../../infra/docker/Dockerfile.api"

[env]
  PORT = "8000"
  LOG_LEVEL = "INFO"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[[services]]
  protocol = "tcp"
  internal_port = 8000

  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [services.concurrency]
    type = "requests"
    hard_limit = 250
    soft_limit = 200

[[services.tcp_checks]]
  interval = "15s"
  timeout = "2s"
  grace_period = "5s"
```

### 3. Deploy Worker to Fly.io

```bash
cd apps/worker

# Create Fly.io app
flyctl apps create prompter-worker

# Set secrets (same as API)
flyctl secrets set DATABASE_URL="..." REDIS_URL="..." ...

# Deploy
flyctl deploy

# Scale
flyctl scale count 2
```

Create `fly.toml`:

```toml
app = "prompter-worker"
primary_region = "iad"

[build]
  dockerfile = "../../infra/docker/Dockerfile.worker"

[env]
  LOG_LEVEL = "INFO"
```

### 4. Deploy Web to Vercel

```bash
cd apps/web

# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod

# Or configure via Vercel Dashboard:
# - Connect GitHub repository
# - Set root directory to apps/web
# - Add environment variables
```

Environment variables:

```
NEXT_PUBLIC_API_BASE_URL=https://prompter-api.fly.dev
NEXT_PUBLIC_APP_URL=https://prompter.site
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
```

### 5. Configure Cloudflare

```bash
# Add domain to Cloudflare
# Enable proxy (orange cloud)

# DNS Records:
# A    @           <Vercel IP>   Proxied
# A    *           <Vercel IP>   Proxied
# CNAME api       prompter-api.fly.dev  Proxied

# SSL/TLS: Full (strict)
# Page Rules:
#   - *.prompter.site/k/* : Cache Everything
```

### 6. Setup Monitoring

**Sentry**

```bash
# Create projects for web, api, worker
# Add DSN to environment variables
```

**Grafana Cloud**

```bash
# Create account
# Get OTLP endpoint
# Add to OTEL_EXPORTER_OTLP_ENDPOINT
```

## Post-Deployment

### 1. Verify Health

```bash
# API health
curl https://api.prompter.site/health

# Web health
curl https://prompter.site
```

### 2. Run Test Scan

```bash
# Login to web app
# Create test brand
# Run scan
# Verify results
```

### 3. Setup Alerts

Configure alerts in Fly.io, Sentry, and Grafana for:
- High error rate
- Slow response times
- Database connection issues
- Queue depth

## Rollback Procedure

### Rollback Web

```bash
# Vercel automatically keeps previous deployments
vercel rollback
```

### Rollback API/Worker

```bash
# Fly.io keeps previous releases
flyctl releases list
flyctl releases rollback <release-id>
```

### Rollback Database

```bash
# Restore from backup
# Or run down migration
cd apps/api
python -m alembic downgrade -1
```

## Scaling

### Horizontal Scaling

```bash
# Scale API
flyctl scale count 4 --app prompter-api

# Scale Worker
flyctl scale count 4 --app prompter-worker
```

### Vertical Scaling

```bash
# Increase resources
flyctl scale vm performance-2x --app prompter-api
```

### Database Scaling

```bash
# For Neon/Supabase: Upgrade plan in dashboard
# For RDS: Use Terraform to change instance class
```

## Maintenance

### Database Backup

```bash
# Automated backups (configured in RDS/Neon/Supabase)
# Manual backup:
pg_dump $DATABASE_URL > backup.sql
```

### Log Rotation

```bash
# Fly.io automatically rotates logs
# Download logs:
flyctl logs --app prompter-api > api.log
```

### Certificate Renewal

Automatically handled by Cloudflare and Fly.io.

## Troubleshooting

### API Not Responding

```bash
# Check logs
flyctl logs --app prompter-api

# Check status
flyctl status --app prompter-api

# Restart
flyctl apps restart prompter-api
```

### Worker Not Processing Jobs

```bash
# Check logs
flyctl logs --app prompter-worker

# Check Redis connection
redis-cli -u $REDIS_URL ping

# Check queue depth
redis-cli -u $REDIS_URL LLEN rq:queue:default
```

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check connection pool
# Review logs for "too many connections"
```

## Security Checklist

- [ ] All secrets set via environment variables
- [ ] HTTPS enforced
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Database backups enabled
- [ ] Monitoring and alerts configured
- [ ] Security headers configured
- [ ] Dependencies up to date
- [ ] Audit logging enabled
- [ ] API keys rotated regularly

