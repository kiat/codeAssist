"""Add enable_code_editor to assignments.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-16 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE assignments ADD COLUMN IF NOT EXISTS enable_code_editor BOOLEAN DEFAULT FALSE"
    )
    op.execute(
        "UPDATE assignments SET enable_code_editor = FALSE WHERE enable_code_editor IS NULL"
    )
    op.execute("ALTER TABLE assignments ALTER COLUMN enable_code_editor SET NOT NULL")


def downgrade():
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS enable_code_editor")
