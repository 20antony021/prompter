# Data Model

## Entity Relationship Diagram

```
User ──┬─── OrgMember ───── Org ──┬─── Brand ──┬─── Competitor
       │                          │            │
       │                          │            ├─── PromptSet ─── PromptSetItem ─── PromptTemplate
       │                          │            │
       │                          │            ├─── ScanRun ─── ScanResult ─── Mention
       │                          │            │
       │                          │            ├─── KnowledgePage
       │                          │            │
       │                          │            └─── HostedSiteBinding ─── HostedDomain
       │                          │
       │                          ├─── PromptTemplate (system)
       │                          │
       │                          ├─── HostedDomain
       │                          │
       │                          ├─── UsageMeter
       │                          │
       │                          ├─── ApiKey
       │                          │
       │                          └─── AuditLog

Plan (reference data)
```

## Core Entities

### User
Represents an authenticated user in the system.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| auth_provider_id | String | Clerk user ID |
| email | String | User email (unique) |
| name | String | Display name |
| created_at | DateTime | Creation timestamp |

**Relationships:**
- Has many `OrgMember` (user can belong to multiple orgs)

---

### Org (Organization)
Represents a customer organization/account.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | String | Organization name |
| slug | String | URL-friendly slug (unique) |
| plan_tier | Enum | Subscription tier (starter/growth/enterprise) |
| stripe_customer_id | String | Stripe customer ID |
| created_at | DateTime | Creation timestamp |

**Relationships:**
- Has many `OrgMember`
- Has many `Brand`
- Has many `PromptTemplate`
- Has many `HostedDomain`
- Has many `UsageMeter`
- Has many `ApiKey`

---

### OrgMember
Junction table linking users to organizations with roles.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| org_id | Integer | Foreign key to Org |
| user_id | Integer | Foreign key to User |
| role | Enum | Role (owner/admin/member) |
| created_at | DateTime | Creation timestamp |

---

### Brand
Represents a brand being tracked for AI visibility.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| org_id | Integer | Foreign key to Org |
| name | String | Brand name |
| website | String | Brand website URL |
| primary_domain | String | Primary domain for hosting |
| created_at | DateTime | Creation timestamp |

**Relationships:**
- Belongs to `Org`
- Has many `Competitor`
- Has many `PromptSet`
- Has many `ScanRun`
- Has many `KnowledgePage`
- Has many `HostedSiteBinding`

---

### Competitor
Competitor brands to track alongside the main brand.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| brand_id | Integer | Foreign key to Brand |
| name | String | Competitor name |
| website | String | Competitor website URL |
| created_at | DateTime | Creation timestamp |

---

### PromptTemplate
Reusable prompt templates.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| org_id | Integer | Foreign key to Org (nullable for system prompts) |
| label | String | Human-readable label |
| text | Text | Prompt text (supports {variables}) |
| locale | String | Language code |
| vertical | String | Industry vertical (saas/ecommerce/etc.) |
| is_system | Boolean | System-provided template |
| created_at | DateTime | Creation timestamp |

---

### PromptSet
Collection of prompts for a brand.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| brand_id | Integer | Foreign key to Brand |
| name | String | Set name |
| description | Text | Description |
| created_at | DateTime | Creation timestamp |

**Relationships:**
- Belongs to `Brand`
- Has many `PromptSetItem`
- Has many `ScanRun`

---

### PromptSetItem
Links prompt templates to prompt sets with variable values.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| prompt_set_id | Integer | Foreign key to PromptSet |
| prompt_template_id | Integer | Foreign key to PromptTemplate |
| variables_json | JSON | Variable substitutions |
| created_at | DateTime | Creation timestamp |

---

### ScanRun
A batch execution of prompts across multiple AI models.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| brand_id | Integer | Foreign key to Brand |
| prompt_set_id | Integer | Foreign key to PromptSet |
| status | Enum | Status (queued/running/done/failed) |
| model_matrix_json | JSON | List of models to test |
| started_at | DateTime | Start timestamp |
| finished_at | DateTime | Completion timestamp |
| created_at | DateTime | Creation timestamp |

**Relationships:**
- Belongs to `Brand`
- Belongs to `PromptSet`
- Has many `ScanResult`

---

### ScanResult
Single prompt response from one AI model.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| scan_run_id | Integer | Foreign key to ScanRun |
| model_name | String | Model identifier |
| prompt_text | Text | Actual prompt sent |
| raw_response | Text | Full LLM response |
| parsed_json | JSON | Structured extraction |
| created_at | DateTime | Creation timestamp |

**Relationships:**
- Belongs to `ScanRun`
- Has many `Mention`

---

### Mention
Extracted brand/competitor mention from a scan result.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| scan_result_id | Integer | Foreign key to ScanResult |
| entity_name | String | Mentioned entity name |
| entity_type | Enum | Type (brand/competitor/other) |
| sentiment | Float | Sentiment score (-1.0 to 1.0) |
| position_index | Integer | Position in response (0-based) |
| confidence | Float | Extraction confidence (0.0 to 1.0) |
| cited_urls_json | JSON | URLs cited with mention |
| created_at | DateTime | Creation timestamp |

---

### KnowledgePage
AI-optimized content page.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| brand_id | Integer | Foreign key to Brand |
| title | String | Page title |
| slug | String | URL slug |
| status | Enum | Status (draft/published/archived) |
| html | Text | Rendered HTML |
| mdx | Text | Source MDX |
| schema_json | JSON | JSON-LD structured data |
| score | Float | Page health score (0-100) |
| published_at | DateTime | Publication timestamp |
| canonical_url | String | Canonical URL |
| path | String | URL path |
| subdomain | String | Subdomain for hosting |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Update timestamp |

---

### HostedDomain
Custom domain for hosting pages.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| org_id | Integer | Foreign key to Org |
| apex_domain | String | Domain name |
| wildcard_enabled | Boolean | Wildcard DNS enabled |
| dns_status | Enum | DNS status (pending/verified/failed) |
| created_at | DateTime | Creation timestamp |

---

### HostedSiteBinding
Maps brand to subdomain.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| brand_id | Integer | Foreign key to Brand |
| hosted_domain_id | Integer | Foreign key to HostedDomain |
| subdomain | String | Subdomain (e.g., "acme") |
| created_at | DateTime | Creation timestamp |

---

### Plan
Subscription plan (reference data).

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| code | String | Plan code (starter/growth/enterprise) |
| name | String | Display name |
| price_monthly | Integer | Price in cents |
| limits_json | JSON | Plan limits |
| created_at | DateTime | Creation timestamp |

---

### UsageMeter
Tracks monthly usage per organization.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| org_id | Integer | Foreign key to Org |
| month | String | Month (YYYY-MM) |
| prompts_used | Integer | Number of prompts run |
| pages_hosted | Integer | Number of pages hosted |
| overage_cents | Integer | Overage charges |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Update timestamp |

---

### ApiKey
API key for programmatic access.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| org_id | Integer | Foreign key to Org |
| key_hash | String | Hashed API key |
| label | String | Key label |
| scopes | Text | Comma-separated scopes |
| created_at | DateTime | Creation timestamp |
| last_used_at | DateTime | Last use timestamp |

---

### AuditLog
Audit trail of user actions.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| org_id | Integer | Foreign key to Org |
| user_id | Integer | Foreign key to User (nullable) |
| action | String | Action performed |
| metadata_json | JSON | Additional context |
| created_at | DateTime | Creation timestamp |

## Indexes

Key indexes for performance:

- `users.auth_provider_id` (unique)
- `users.email` (unique)
- `orgs.slug` (unique)
- `brands.org_id`
- `scan_runs.brand_id, status`
- `scan_results.scan_run_id`
- `mentions.entity_name`
- `mentions.entity_type`
- `knowledge_pages.brand_id, status`
- `audit_logs.org_id, created_at`

