"""Add assignment AI feedback API key.

Revision ID: f7a8b9c0d1e2
Revises: e5f6a7b8c9d0
Create Date: 2026-07-05 00:00:00.000000

"""
from alembic import op


revision = "f7a8b9c0d1e2"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_api_key VARCHAR DEFAULT ''")


def downgrade():
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_api_key")
