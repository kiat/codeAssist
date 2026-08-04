"""Add student submission insight history.

Revision ID: e6f7a8b9c0d2
Revises: d6e7f8a9b0c1
Create Date: 2026-07-26 00:00:00.000000

"""
from alembic import op


revision = "e6f7a8b9c0d2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """CREATE TABLE IF NOT EXISTS student_submission_insights (
            id UUID PRIMARY KEY,
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            assignment_id UUID NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
            submission_id UUID NOT NULL UNIQUE REFERENCES submissions(id) ON DELETE CASCADE,
            insights JSON,
            summary TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_student_submission_insights_student_assignment_created_at
           ON student_submission_insights (student_id, assignment_id, created_at DESC)"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_student_submission_insights_submission
           ON student_submission_insights (submission_id)"""
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_student_submission_insights_submission")
    op.execute(
        "DROP INDEX IF EXISTS idx_student_submission_insights_student_assignment_created_at"
    )
    op.execute("DROP TABLE IF EXISTS student_submission_insights")
