"""Add assignment submission_files.

Revision ID: b8c9d0e1f2a3
Revises: 51f7b0498833
Create Date: 2026-10-27 00:00:00.000000

"""
from alembic import op


revision = "b8c9d0e1f2a3"
down_revision = "51f7b0498833"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS submission_files JSON")


def downgrade():
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS submission_files")
