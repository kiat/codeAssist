"""Add grade publish fields to assignments.

Revision ID: a3b4c5d6e7f8
Revises: e6f7a8b9c0d2
Create Date: 2026-08-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a3b4c5d6e7f8'
down_revision = 'e6f7a8b9c0d2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('assignments', sa.Column('hold_grades', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('assignments', sa.Column('grades_published', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('assignments', sa.Column('grades_published_at', postgresql.TIMESTAMP(timezone=True), nullable=True))


def downgrade():
    op.drop_column('assignments', 'grades_published_at')
    op.drop_column('assignments', 'grades_published')
    op.drop_column('assignments', 'hold_grades')
