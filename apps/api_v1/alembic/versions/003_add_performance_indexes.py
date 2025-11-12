"""Add composite indexes for query performance.

Revision ID: 003
Revises: 002
Create Date: 2025-11-06 00:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_label = None
depends_on = None


def upgrade():
    """Add composite indexes for common query patterns."""
    # Brands
    op.create_index('ix_brands_org_id_created_at', 'brands', ['org_id', 'created_at'], unique=False)
    
    # Scan runs - frequently filtered by brand_id and sorted by created_at
    op.create_index('ix_scan_runs_brand_id_created_at', 'scan_runs', ['brand_id', 'created_at'], unique=False)
    op.create_index('ix_scan_runs_brand_id_status', 'scan_runs', ['brand_id', 'status'], unique=False)
    
    # Mentions - commonly joined and filtered
    op.create_index('ix_mentions_scan_result_id', 'mentions', ['scan_result_id'], unique=False)
    op.create_index('ix_mentions_entity_name', 'mentions', ['entity_name'], unique=False)
    
    # Knowledge pages
    op.create_index('ix_knowledge_pages_brand_id_created_at', 'knowledge_pages', ['brand_id', 'created_at'], unique=False)
    op.create_index('ix_knowledge_pages_brand_id_status', 'knowledge_pages', ['brand_id', 'status'], unique=False)
    
    # Audit logs - frequently queried by org and time range
    op.create_index('ix_audit_logs_org_id_created_at', 'audit_logs', ['org_id', 'created_at'], unique=False)


def downgrade():
    """Remove composite indexes."""
    op.drop_index('ix_audit_logs_org_id_created_at', table_name='audit_logs')
    op.drop_index('ix_knowledge_pages_brand_id_status', table_name='knowledge_pages')
    op.drop_index('ix_knowledge_pages_brand_id_created_at', table_name='knowledge_pages')
    op.drop_index('ix_mentions_entity_name', table_name='mentions')
    op.drop_index('ix_mentions_scan_result_id', table_name='mentions')
    op.drop_index('ix_scan_runs_brand_id_status', table_name='scan_runs')
    op.drop_index('ix_scan_runs_brand_id_created_at', table_name='scan_runs')
    op.drop_index('ix_brands_org_id_created_at', table_name='brands')

