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
    op.add_column('assignments', sa.Column('enable_code_editor', sa.Boolean(), server_default='false', nullable=False))


def downgrade():
    op.drop_column('assignments', 'enable_code_editor')
