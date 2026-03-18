"""add session_token to users

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("session_token", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "session_token")
