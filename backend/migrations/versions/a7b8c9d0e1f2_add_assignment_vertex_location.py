"""Add assignment Vertex AI location override.

Revision ID: a7b8c9d0e1f2
Revises: a3b4c5d6e7f8
Create Date: 2026-08-04 00:00:00.000000

"""
from alembic import op


revision = "a7b8c9d0e1f2"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_vertex_location VARCHAR")


def downgrade():
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_vertex_location")
