"""Add pricing plans and usage tracking with billing cycles.

Revision ID: 004
Revises: 003
Create Date: 2025-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_label = None
depends_on = None


def upgrade():
    """Add plan_tier, billing cycle fields to orgs and create org_monthly_usage table."""
    
    # Update PlanTier enum to include 'pro' and 'business' (removing 'growth')
    # First, add the new enum values
    op.execute("ALTER TYPE plantier ADD VALUE IF NOT EXISTS 'pro'")
    op.execute("ALTER TYPE plantier ADD VALUE IF NOT EXISTS 'business'")
    
    # Note: Removing 'growth' value requires recreating the enum or migrating data
    # For now, we'll keep both old and new values for backward compatibility
    # In production, you'd migrate data from 'growth' to 'pro' first
    
    # Add billing cycle columns to orgs table
    op.add_column('orgs', sa.Column('seats_limit', sa.Integer(), nullable=True))
    op.add_column('orgs', sa.Column('billing_cycle_anchor', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('orgs', sa.Column('current_period_start', sa.DateTime(), nullable=True))
    op.add_column('orgs', sa.Column('current_period_end', sa.DateTime(), nullable=True))
    
    # Create org_monthly_usage table with billing periods
    # Using BIGINT for usage counters to handle very high volumes
    op.create_table(
        'org_monthly_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', sa.Integer(), sa.ForeignKey('orgs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('scans_used', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('prompts_used', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('ai_pages_generated', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('org_id', 'period_start', name='uq_usage_org_period'),
        # CHECK constraints to prevent negative usage (no refunds)
        sa.CheckConstraint('scans_used >= 0', name='ck_scans_non_negative'),
        sa.CheckConstraint('prompts_used >= 0', name='ck_prompts_non_negative'),
        sa.CheckConstraint('ai_pages_generated >= 0', name='ck_pages_non_negative'),
    )
    
    # Create indexes
    op.create_index(op.f('ix_org_monthly_usage_org_id'), 'org_monthly_usage', ['org_id'], unique=False)
    op.create_index(op.f('ix_org_monthly_usage_period_start'), 'org_monthly_usage', ['period_start'], unique=False)
    op.create_index(op.f('ix_org_monthly_usage_period_end'), 'org_monthly_usage', ['period_end'], unique=False)
    
    # Composite index for efficient lookups (org_id, period_start)
    # This is the primary query pattern for usage checks
    op.create_index(
        'ix_org_monthly_usage_org_period', 
        'org_monthly_usage', 
        ['org_id', 'period_start'], 
        unique=False
    )


def downgrade():
    """Remove plan_tier updates, billing cycle fields, and org_monthly_usage table."""
    
    # Drop indexes (including composite index)
    op.drop_index('ix_org_monthly_usage_org_period', table_name='org_monthly_usage')
    op.drop_index(op.f('ix_org_monthly_usage_period_end'), table_name='org_monthly_usage')
    op.drop_index(op.f('ix_org_monthly_usage_period_start'), table_name='org_monthly_usage')
    op.drop_index(op.f('ix_org_monthly_usage_org_id'), table_name='org_monthly_usage')
    
    # Drop org_monthly_usage table (also drops CHECK constraints)
    op.drop_table('org_monthly_usage')
    
    # Drop billing cycle columns
    op.drop_column('orgs', 'current_period_end')
    op.drop_column('orgs', 'current_period_start')
    op.drop_column('orgs', 'billing_cycle_anchor')
    op.drop_column('orgs', 'seats_limit')
    
    # Note: Removing enum values is complex in PostgreSQL
    # In production, you'd need to handle this carefully
    # This downgrade assumes you keep the new enum values

