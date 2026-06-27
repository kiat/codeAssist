"""Add assignment AI feedback prompt and input settings.

Revision ID: f6a7b8c9d0e1
Revises: c3d4e5f6a7b8
Create Date: 2026-06-26 00:00:00.000000

"""
from alembic import op


revision = "f6a7b8c9d0e1"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_prompts JSON")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_allowed_inputs JSON")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_max_requests INTEGER")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_wait_seconds INTEGER DEFAULT 0")


def downgrade():
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_wait_seconds")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_max_requests")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_allowed_inputs")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_prompts")
