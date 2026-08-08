"""Add enable_code_editor to assignments.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Idempotent: some databases already have this column from before the
    # migration-head split was reconciled, so only add it when missing. The
    # check-then-add isn't atomic, so if two workers race and both see the
    # column missing, fall back on catching the resulting "column already
    # exists" error from whichever one loses the race.
    bind = op.get_bind()
    columns = [c["name"] for c in sa.inspect(bind).get_columns("assignments")]
    if "enable_code_editor" not in columns:
        try:
            op.add_column(
                "assignments",
                sa.Column("enable_code_editor", sa.Boolean(), server_default="false", nullable=False),
            )
        except ProgrammingError as e:
            if "already exists" not in str(e):
                raise


def downgrade():
    op.drop_column('assignments', 'enable_code_editor')
