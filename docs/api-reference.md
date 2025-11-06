# API Reference

## Base URL

```
Production: https://api.prompter.site/v1
Development: http://localhost:8000/v1
```

## Authentication

All API requests require authentication via JWT token from Clerk.

```bash
Authorization: Bearer <token>
```

## Rate Limiting

- **Starter**: 60 requests/minute
- **Growth**: 300 requests/minute
- **Enterprise**: 1000 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1234567890
```

## Error Responses

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Endpoints

### Health Check

**GET** `/health`

Health check endpoint (no auth required).

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Brands

#### Create Brand

**POST** `/brands`

Create a new brand.

Request:
```json
{
  "org_id": 1,
  "name": "AcmeCRM",
  "website": "https://acmecrm.com",
  "primary_domain": "acmecrm.com"
}
```

Response:
```json
{
  "id": 1,
  "org_id": 1,
  "name": "AcmeCRM",
  "website": "https://acmecrm.com",
  "primary_domain": "acmecrm.com",
  "created_at": "2024-01-01T00:00:00Z",
  "competitors": []
}
```

#### Get Brand

**GET** `/brands/{brand_id}`

Get brand by ID.

Response:
```json
{
  "id": 1,
  "org_id": 1,
  "name": "AcmeCRM",
  "website": "https://acmecrm.com",
  "primary_domain": "acmecrm.com",
  "created_at": "2024-01-01T00:00:00Z",
  "competitors": [
    {
      "id": 1,
      "brand_id": 1,
      "name": "SalesFlow",
      "website": "https://salesflow.com",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### List Brands

**GET** `/brands?org_id={org_id}`

List brands for organization.

Response:
```json
[
  {
    "id": 1,
    "org_id": 1,
    "name": "AcmeCRM",
    "website": "https://acmecrm.com",
    "primary_domain": "acmecrm.com",
    "created_at": "2024-01-01T00:00:00Z",
    "competitors": []
  }
]
```

#### Update Brand

**PUT** `/brands/{brand_id}`

Update brand.

Request:
```json
{
  "name": "AcmeCRM Pro",
  "website": "https://acmecrm.com"
}
```

#### Add Competitor

**POST** `/brands/{brand_id}/competitors`

Add competitor to brand.

Request:
```json
{
  "name": "SalesFlow",
  "website": "https://salesflow.com"
}
```

Response:
```json
{
  "id": 1,
  "brand_id": 1,
  "name": "SalesFlow",
  "website": "https://salesflow.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### Scans

#### Create Scan Run

**POST** `/scans`

Create and queue a new scan run.

Request:
```json
{
  "brand_id": 1,
  "prompt_set_id": 1,
  "models": ["gpt-4", "claude-3-opus", "gemini-pro"]
}
```

Response:
```json
{
  "id": 1,
  "brand_id": 1,
  "prompt_set_id": 1,
  "status": "queued",
  "model_matrix_json": ["gpt-4", "claude-3-opus", "gemini-pro"],
  "started_at": null,
  "finished_at": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Get Scan Run

**GET** `/scans/{scan_id}`

Get scan run with results.

Response:
```json
{
  "id": 1,
  "brand_id": 1,
  "prompt_set_id": 1,
  "status": "done",
  "model_matrix_json": ["gpt-4"],
  "started_at": "2024-01-01T00:00:00Z",
  "finished_at": "2024-01-01T00:05:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "results": [
    {
      "id": 1,
      "scan_run_id": 1,
      "model_name": "gpt-4",
      "prompt_text": "What is the best CRM?",
      "raw_response": "AcmeCRM is one of the top CRM solutions...",
      "parsed_json": {},
      "created_at": "2024-01-01T00:02:00Z"
    }
  ]
}
```

#### List Scan Runs

**GET** `/scans?brand_id={brand_id}`

List scan runs for brand.

Response:
```json
[
  {
    "id": 1,
    "brand_id": 1,
    "prompt_set_id": 1,
    "status": "done",
    "model_matrix_json": ["gpt-4"],
    "started_at": "2024-01-01T00:00:00Z",
    "finished_at": "2024-01-01T00:05:00Z",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### List Mentions

**GET** `/scans/mentions?brand_id={brand_id}&limit={limit}`

List mentions for brand.

Query Parameters:
- `brand_id`: Brand ID (required)
- `limit`: Max results (default: 100, max: 1000)

Response:
```json
[
  {
    "id": 1,
    "scan_result_id": 1,
    "entity_name": "AcmeCRM",
    "entity_type": "brand",
    "sentiment": 0.8,
    "position_index": 0,
    "confidence": 0.9,
    "cited_urls_json": ["https://acmecrm.com"],
    "created_at": "2024-01-01T00:02:00Z"
  }
]
```

---

### Knowledge Pages

#### Create Knowledge Page

**POST** `/pages`

Create new knowledge page (starts generation).

Request:
```json
{
  "brand_id": 1,
  "title": "AcmeCRM - Modern CRM Solution",
  "urls_to_crawl": ["https://acmecrm.com", "https://acmecrm.com/features"],
  "vertical": "saas"
}
```

Response:
```json
{
  "id": 1,
  "brand_id": 1,
  "title": "AcmeCRM - Modern CRM Solution",
  "slug": "acmecrm-modern-crm-solution",
  "status": "draft",
  "score": null,
  "published_at": null,
  "canonical_url": null,
  "path": null,
  "subdomain": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Get Knowledge Page

**GET** `/pages/{page_id}`

Get knowledge page with full content.

Response:
```json
{
  "id": 1,
  "brand_id": 1,
  "title": "AcmeCRM - Modern CRM Solution",
  "slug": "acmecrm-modern-crm-solution",
  "status": "published",
  "score": 85.5,
  "published_at": "2024-01-01T00:10:00Z",
  "canonical_url": "https://acme.prompter.site/k/acmecrm-modern-crm-solution",
  "path": "/k/acmecrm-modern-crm-solution",
  "subdomain": "acme",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:10:00Z",
  "html": "<div>...</div>",
  "mdx": "## AcmeCRM Overview...",
  "schema_json": {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "AcmeCRM"
  }
}
```

#### List Knowledge Pages

**GET** `/pages?brand_id={brand_id}`

List knowledge pages for brand.

Response:
```json
[
  {
    "id": 1,
    "brand_id": 1,
    "title": "AcmeCRM - Modern CRM Solution",
    "slug": "acmecrm-modern-crm-solution",
    "status": "published",
    "score": 85.5,
    "published_at": "2024-01-01T00:10:00Z",
    "canonical_url": "https://acme.prompter.site/k/acmecrm-modern-crm-solution",
    "path": "/k/acmecrm-modern-crm-solution",
    "subdomain": "acme",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:10:00Z"
  }
]
```

#### Update Knowledge Page

**PUT** `/pages/{page_id}`

Update knowledge page.

Request:
```json
{
  "title": "AcmeCRM - Updated Title",
  "mdx": "## Updated content...",
  "canonical_url": "https://acmecrm.com/about"
}
```

#### Publish Knowledge Page

**PUT** `/pages/{page_id}/publish`

Publish knowledge page to subdomain.

Request:
```json
{
  "subdomain": "acme"
}
```

Response:
```json
{
  "id": 1,
  "brand_id": 1,
  "title": "AcmeCRM - Modern CRM Solution",
  "slug": "acmecrm-modern-crm-solution",
  "status": "published",
  "score": 85.5,
  "published_at": "2024-01-01T00:10:00Z",
  "canonical_url": "https://acme.prompter.site/k/acmecrm-modern-crm-solution",
  "path": "/k/acmecrm-modern-crm-solution",
  "subdomain": "acme",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:10:00Z"
}
```

---

## Webhooks

### Stripe Webhook

**POST** `/webhooks/stripe`

Stripe webhook endpoint for billing events.

Handles:
- `checkout.session.completed`
- `invoice.paid`
- `invoice.payment_failed`
- `customer.subscription.updated`
- `customer.subscription.deleted`

---

## Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

## SDKs

### JavaScript/TypeScript

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.prompter.site/v1',
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

// Create brand
const brand = await api.post('/brands', {
  org_id: 1,
  name: 'AcmeCRM',
  website: 'https://acmecrm.com',
});

// Create scan
const scan = await api.post('/scans', {
  brand_id: brand.data.id,
  prompt_set_id: 1,
  models: ['gpt-4', 'claude-3-opus'],
});
```

### Python

```python
import httpx

client = httpx.Client(
    base_url='https://api.prompter.site/v1',
    headers={'Authorization': f'Bearer {token}'},
)

# Create brand
brand = client.post('/brands', json={
    'org_id': 1,
    'name': 'AcmeCRM',
    'website': 'https://acmecrm.com',
}).json()

# Create scan
scan = client.post('/scans', json={
    'brand_id': brand['id'],
    'prompt_set_id': 1,
    'models': ['gpt-4', 'claude-3-opus'],
}).json()
```

---

## Interactive Documentation

Visit [https://api.prompter.site/docs](https://api.prompter.site/docs) for interactive API documentation with Swagger UI.

