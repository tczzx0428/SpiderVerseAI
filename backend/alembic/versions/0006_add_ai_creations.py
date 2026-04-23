"""add ai_creations table

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-23 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ai_creations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=True),
        sa.Column('conversation', postgresql.JSON(astext_type=sa.Text()), nullable=True, default=list),
        sa.Column('status', sa.String(length=32), nullable=False, default='chatting'),
        sa.Column('generated_code', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('app_id', sa.Integer(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=False, default=0),
        sa.Column('progress_message', sa.String(length=512), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_creations_id'), 'ai_creations', ['id'], unique=False)
    op.create_index(op.f('ix_ai_creations_user_id'), 'ai_creations', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_creations_user_id'), table_name='ai_creations')
    op.drop_index(op.f('ix_ai_creations_id'), table_name='ai_creations')
    op.drop_table('ai_creations')