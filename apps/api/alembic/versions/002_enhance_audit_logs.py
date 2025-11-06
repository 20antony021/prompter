"""Enhance audit logs with detailed tracking fields.

Revision ID: 002
Revises: 001
Create Date: 2025-11-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'  # Update this to match your latest migration
branch_label = None
depends_on = None


def upgrade():
    """Add enhanced audit log fields."""
    # Add new columns to audit_logs
    op.add_column('audit_logs', sa.Column('resource_type', sa.String(length=100), nullable=True))
    op.add_column('audit_logs', sa.Column('resource_id', sa.Integer(), nullable=True))
    op.add_column('audit_logs', sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('audit_logs', sa.Column('ip_address', sa.String(length=45), nullable=True))
    op.add_column('audit_logs', sa.Column('user_agent', sa.Text(), nullable=True))
    op.add_column('audit_logs', sa.Column('request_id', sa.String(length=100), nullable=True))
    
    # Create indexes for better query performance
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_id'), 'audit_logs', ['resource_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_request_id'), 'audit_logs', ['request_id'], unique=False)
    
    # Migrate action column to use enum if not already
    # Note: This assumes action column already exists as String
    # In production, you may need to handle existing data migration


def downgrade():
    """Remove enhanced audit log fields."""
    op.drop_index(op.f('ix_audit_logs_request_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_type'), table_name='audit_logs')
    
    op.drop_column('audit_logs', 'request_id')
    op.drop_column('audit_logs', 'user_agent')
    op.drop_column('audit_logs', 'ip_address')
    op.drop_column('audit_logs', 'details')
    op.drop_column('audit_logs', 'resource_id')
    op.drop_column('audit_logs', 'resource_type')

