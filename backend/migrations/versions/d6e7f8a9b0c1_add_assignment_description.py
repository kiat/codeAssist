"""Add assignment description.

Revision ID: d6e7f8a9b0c1
Revises: c4d5e6f7a8b9
Create Date: 2026-07-26 00:00:00.000000

"""
from alembic import op


revision = "d6e7f8a9b0c1"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS description TEXT")


def downgrade():
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS description")
