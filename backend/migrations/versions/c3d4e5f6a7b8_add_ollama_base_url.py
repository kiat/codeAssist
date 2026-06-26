"""Add ollama_base_url to courses.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS ollama_base_url VARCHAR DEFAULT ''")


def downgrade():
    op.execute("ALTER TABLE courses DROP COLUMN IF EXISTS ollama_base_url")
