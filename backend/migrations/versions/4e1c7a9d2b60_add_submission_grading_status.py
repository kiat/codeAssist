"""Add submission grading status for async grading (#148).

Revision ID: 4e1c7a9d2b60
Revises: b8c9d0e1f2a3
Create Date: 2026-10-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "4e1c7a9d2b60"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("submissions") as batch_op:
        batch_op.add_column(sa.Column(
            "status", sa.String(16), nullable=False, server_default="graded"
        ))
        batch_op.add_column(sa.Column(
            "grading_started_at", postgresql.TIMESTAMP(timezone=True), nullable=True
        ))
        batch_op.create_check_constraint(
            "ck_submissions_status",
            "status IN ('pending', 'running', 'graded', 'failed')",
        )


def downgrade():
    with op.batch_alter_table("submissions") as batch_op:
        batch_op.drop_constraint("ck_submissions_status", type_="check")
        batch_op.drop_column("grading_started_at")
        batch_op.drop_column("status")
