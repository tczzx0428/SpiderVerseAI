"""add ai_model_configs table

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-23 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ai_model_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('model_id', sa.String(length=128), nullable=False),
        sa.Column('api_key', sa.String(length=512), nullable=False),
        sa.Column('base_url', sa.String(length=512), nullable=False),
        sa.Column('usage', sa.String(length=16), nullable=False, default='chat'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_model_configs_id'), 'ai_model_configs', ['id'], unique=False)

    op.execute("""
        INSERT INTO ai_model_configs (name, provider, model_id, api_key, base_url, usage, is_enabled, priority, created_by, created_at, updated_at)
        VALUES ('DeepSeek Chat', 'deepseek', 'deepseek-chat', '', 'https://api.deepseek.com/v1', 'both', true, 0, 1, NOW(), NOW())
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_model_configs_id'), table_name='ai_model_configs')
    op.drop_table('ai_model_configs')