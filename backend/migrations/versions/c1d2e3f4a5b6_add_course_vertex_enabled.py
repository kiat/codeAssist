"""Add course vertex_enabled flag.

Revision ID: c1d2e3f4a5b6
Revises: a7b8c9d0e1f2
Create Date: 2026-11-15 00:00:00.000000

"""
from alembic import op


revision = "c1d2e3f4a5b6"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS vertex_enabled BOOLEAN NOT NULL DEFAULT FALSE"
    )


def downgrade():
    op.execute("ALTER TABLE courses DROP COLUMN IF EXISTS vertex_enabled")
