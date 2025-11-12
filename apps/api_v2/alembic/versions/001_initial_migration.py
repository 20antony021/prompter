"""Initial migration with lookout schema

Revision ID: 001
Revises: 
Create Date: 2025-11-11 19:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def table_exists(table_name):
    """Check if table exists in database"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    # Create enums (skip if already exists)
    op.execute("DO $$ BEGIN CREATE TYPE plan AS ENUM ('free', 'basic', 'pro', 'enterprise'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE model AS ENUM ('openai', 'claude', 'google'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("""DO $$ BEGIN CREATE TYPE geo_region AS ENUM (
        'global', 'us', 'eu', 'uk', 'de', 'fr', 'es', 'it', 'in', 'jp', 
        'cn', 'au', 'ca', 'br', 'mx', 'ar', 'sa', 'ae', 'il', 'tr'
    ); EXCEPTION WHEN duplicate_object THEN null; END $$;""")
    op.execute("DO $$ BEGIN CREATE TYPE prompt_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE mention_type AS ENUM ('direct', 'indirect', 'competitive'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE sentiment AS ENUM ('positive', 'negative', 'neutral'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create user table (skip if exists)
    if not table_exists('user'):
        op.create_table('user',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('image', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('stripe_customer_id', sa.String(), nullable=True),
            sa.Column('stripe_subscription_id', sa.String(), nullable=True),
            sa.Column('stripe_price_id', sa.String(), nullable=True),
            sa.Column('stripe_current_period_end', sa.DateTime(), nullable=True),
            sa.Column('plan', postgresql.ENUM(name='plan', create_type=False), nullable=False, server_default='free'),
            sa.Column('plan_status', sa.String(), nullable=False, server_default='active'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email')
        )
    
    # Create session table
    if not table_exists('session'):
        op.create_table('session',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
        )
    
    # Create account table
    if not table_exists('account'):
        op.create_table('account',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.Column('provider_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('id_token', sa.Text(), nullable=True),
        sa.Column('access_token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('refresh_token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('scope', sa.String(), nullable=True),
        sa.Column('password', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
    
    # Create verification table
    if not table_exists('verification'):
        op.create_table('verification',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('identifier', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
        )
    
    # Create topics table
    if not table_exists('topics'):
        op.create_table('topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('logo', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
    
    # Create prompts table
    if not table_exists('prompts'):
        op.create_table('prompts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', postgresql.ENUM(name='prompt_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('geo_region', postgresql.ENUM(name='geo_region', create_type=False), nullable=False, server_default='global'),
        sa.Column('visibility_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
    
    # Create prompt_results table
    if not table_exists('prompt_results'):
        op.create_table('prompt_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model', postgresql.ENUM(name='model', create_type=False), nullable=False),
        sa.Column('response_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', postgresql.ENUM(name='prompt_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('results', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('sources', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('citations', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('search_queries', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('grounding_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prompt_id', 'model', name='ai_model_results_prompt_model_unique')
        )
    
    # Create mentions table
    if not table_exists('mentions'):
        op.create_table('mentions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_result_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model', postgresql.ENUM(name='model', create_type=False), nullable=False),
        sa.Column('mention_type', postgresql.ENUM(name='mention_type', create_type=False), nullable=False),
        sa.Column('position', sa.Numeric(), nullable=True),
        sa.Column('context', sa.Text(), nullable=False),
        sa.Column('sentiment', postgresql.ENUM(name='sentiment', create_type=False), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_result_id'], ['prompt_results.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
    
    # Create indexes (use IF NOT EXISTS)
    op.execute("CREATE INDEX IF NOT EXISTS ix_topics_user_id ON topics (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prompts_topic_id ON prompts (topic_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prompts_user_id ON prompts (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prompts_status ON prompts (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prompt_results_prompt_id ON prompt_results (prompt_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mentions_prompt_id ON mentions (prompt_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mentions_topic_id ON mentions (topic_id)")


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_mentions_topic_id')
    op.drop_index('ix_mentions_prompt_id')
    op.drop_index('ix_prompt_results_prompt_id')
    op.drop_index('ix_prompts_status')
    op.drop_index('ix_prompts_user_id')
    op.drop_index('ix_prompts_topic_id')
    op.drop_index('ix_topics_user_id')
    
    op.drop_table('mentions')
    op.drop_table('prompt_results')
    op.drop_table('prompts')
    op.drop_table('topics')
    op.drop_table('verification')
    op.drop_table('account')
    op.drop_table('session')
    op.drop_table('user')
    
    # Drop enums
    op.execute('DROP TYPE sentiment')
    op.execute('DROP TYPE mention_type')
    op.execute('DROP TYPE prompt_status')
    op.execute('DROP TYPE geo_region')
    op.execute('DROP TYPE model')
    op.execute('DROP TYPE plan')
