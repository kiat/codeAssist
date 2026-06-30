"""Add enable_code_editor to assignments.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS enable_code_editor BOOLEAN DEFAULT 'false' NOT NULL")


def downgrade():
    op.drop_column('assignments', 'enable_code_editor')
