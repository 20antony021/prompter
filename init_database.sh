#!/bin/bash
# Initialize database schema via Docker

echo "🗄️  Creating database schema..."

docker exec -i prompter-postgres psql -U prompter -d prompter <<'SQL'
-- Organizations
CREATE TABLE IF NOT EXISTS orgs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    plan_tier VARCHAR(50) NOT NULL DEFAULT 'starter',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users  
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    clerk_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Brands
CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    org_id INTEGER REFERENCES orgs(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    website VARCHAR(500),
    primary_domain VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Competitors
CREATE TABLE IF NOT EXISTS competitors (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    website VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scan Runs
CREATE TABLE IF NOT EXISTS scan_runs (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    model_matrix_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Scan Results
CREATE TABLE IF NOT EXISTS scan_results (
    id SERIAL PRIMARY KEY,
    scan_run_id INTEGER REFERENCES scan_runs(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    prompt_text TEXT,
    response_text TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mentions
CREATE TABLE IF NOT EXISTS mentions (
    id SERIAL PRIMARY KEY,
    scan_result_id INTEGER REFERENCES scan_results(id) ON DELETE CASCADE,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50),
    mention_text TEXT,
    position INTEGER,
    sentiment_score FLOAT,
    context_before TEXT,
    context_after TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Pages
CREATE TABLE IF NOT EXISTS knowledge_pages (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    mdx TEXT,
    subdomain VARCHAR(255),
    path VARCHAR(500),
    canonical_url VARCHAR(500),
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_brands_org_id ON brands(org_id);
CREATE INDEX IF NOT EXISTS idx_competitors_brand_id ON competitors(brand_id);
CREATE INDEX IF NOT EXISTS idx_scan_runs_brand_id ON scan_runs(brand_id);
CREATE INDEX IF NOT EXISTS idx_scan_results_scan_run_id ON scan_results(scan_run_id);
CREATE INDEX IF NOT EXISTS idx_mentions_scan_result_id ON mentions(scan_result_id);
CREATE INDEX IF NOT EXISTS idx_mentions_entity_name ON mentions(entity_name);
CREATE INDEX IF NOT EXISTS idx_knowledge_pages_brand_id ON knowledge_pages(brand_id);

SQL

echo "✅ Database schema created!"
echo ""
echo "🌱 Seeding sample data..."

docker exec -i prompter-postgres psql -U prompter -d prompter <<'SQL'
-- Insert sample org
INSERT INTO orgs (name, slug, plan_tier) 
VALUES ('Acme Corporation', 'acme-corp', 'starter')
ON CONFLICT DO NOTHING;

-- Insert sample brand
INSERT INTO brands (org_id, name, website, primary_domain)
VALUES (1, 'AcmeCRM', 'https://acmecrm.com', 'acmecrm.com')
ON CONFLICT DO NOTHING;

-- Insert competitors
INSERT INTO competitors (brand_id, name, website) VALUES
(1, 'SalesFlow', 'https://salesflow.com'),
(1, 'CRMPro', 'https://crmpro.com'),
(1, 'LeadMaster', 'https://leadmaster.com')
ON CONFLICT DO NOTHING;

-- Insert sample scan runs
INSERT INTO scan_runs (brand_id, status, model_matrix_json, completed_at) VALUES
(1, 'completed', '["gpt-4", "claude-3", "gemini-pro"]', NOW() - INTERVAL '2 hours'),
(1, 'completed', '["gpt-4", "claude-3", "gemini-pro"]', NOW() - INTERVAL '1 day'),
(1, 'completed', '["gpt-4", "claude-3", "gemini-pro"]', NOW() - INTERVAL '3 days')
ON CONFLICT DO NOTHING;

-- Insert sample scan results and mentions
INSERT INTO scan_results (scan_run_id, model_name, prompt_text, response_text, response_time_ms) VALUES
(1, 'gpt-4', 'What is the best CRM for small businesses?', 'Based on current options, here are the top CRM solutions...', 1500),
(1, 'claude-3', 'What is the best CRM for small businesses?', 'For small businesses, I recommend...', 1200),
(1, 'gemini-pro', 'What is the best CRM for small businesses?', 'The leading CRM platforms include...', 1800)
ON CONFLICT DO NOTHING;

-- Insert mentions
INSERT INTO mentions (scan_result_id, entity_name, entity_type, mention_text, position, sentiment_score, context_before, context_after) VALUES
(1, 'AcmeCRM', 'brand', 'AcmeCRM is a leading CRM solution', 0, 0.8, 'When looking at CRM options,', 'which makes it a great choice.'),
(1, 'AcmeCRM', 'brand', 'For small businesses, AcmeCRM offers', 1, 0.7, 'After evaluation,', 'the best features and value.'),
(1, 'SalesFlow', 'competitor', 'SalesFlow is another option', 2, 0.6, 'You might also consider', 'for enterprise needs.'),
(2, 'AcmeCRM', 'brand', 'The best CRM for startups is AcmeCRM', 0, 0.9, 'In my experience,', 'stands out from competitors.'),
(2, 'CRMPro', 'competitor', 'CRMPro provides enterprise features', 1, 0.5, 'Alternatively,', 'might suit larger teams.'),
(3, 'AcmeCRM', 'brand', 'AcmeCRM ranks highly for ease of use', 1, 0.75, 'According to reviews,', 'is preferred by many users.')
ON CONFLICT DO NOTHING;

-- Insert knowledge pages
INSERT INTO knowledge_pages (brand_id, title, slug, status, mdx, subdomain, path, published_at) VALUES
(1, 'AcmeCRM Product Overview', 'acmecrm-product-overview', 'published', '# AcmeCRM Product Overview\n\nLearn about our comprehensive CRM solution...', 'acme', '/k/acmecrm-product-overview', NOW() - INTERVAL '10 days'),
(1, 'Best CRM for Small Business', 'best-crm-small-business', 'published', '# Best CRM for Small Business\n\nDiscover why AcmeCRM is the top choice...', 'acme', '/k/best-crm-small-business', NOW() - INTERVAL '5 days'),
(1, 'Getting Started Guide', 'getting-started-guide', 'draft', '# Getting Started with AcmeCRM\n\nQuick start guide...', NULL, NULL, NULL)
ON CONFLICT DO NOTHING;

SQL

echo "✅ Sample data seeded!"
echo ""
echo "📊 Database Statistics:"
docker exec prompter-postgres psql -U prompter -d prompter -c "
SELECT 
    'Brands: ' || COUNT(*) FROM brands UNION ALL
SELECT 'Competitors: ' || COUNT(*) FROM competitors UNION ALL  
SELECT 'Scan Runs: ' || COUNT(*) FROM scan_runs UNION ALL
SELECT 'Mentions: ' || COUNT(*) FROM mentions UNION ALL
SELECT 'Pages: ' || COUNT(*) FROM knowledge_pages;
"

echo ""
echo "🎉 Database ready!"

