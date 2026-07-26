"""Add allow_file_upload to assignments.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE assignments ADD COLUMN IF NOT EXISTS allow_file_upload BOOLEAN DEFAULT TRUE"
    )
    op.execute(
        "UPDATE assignments SET allow_file_upload = TRUE WHERE allow_file_upload IS NULL"
    )
    op.execute("ALTER TABLE assignments ALTER COLUMN allow_file_upload SET NOT NULL")


def downgrade():
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS allow_file_upload")
