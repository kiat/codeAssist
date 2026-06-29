"""Add ai_feedback_requests table for per-student usage tracking.

Revision ID: a2b3c4d5e6f7
Revises: 45b5cf6cc787
Create Date: 2026-06-29 00:00:00.000000

"""
from alembic import op


revision = "a2b3c4d5e6f7"
down_revision = "45b5cf6cc787"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """CREATE TABLE IF NOT EXISTS ai_feedback_requests (
            id VARCHAR PRIMARY KEY,
            student_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            assignment_id VARCHAR NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
            prompt_id VARCHAR,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_ai_feedback_requests_student_assignment
           ON ai_feedback_requests (student_id, assignment_id)"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_ai_feedback_requests_last_request
           ON ai_feedback_requests (student_id, assignment_id, created_at DESC)"""
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_ai_feedback_requests_last_request")
    op.execute("DROP INDEX IF EXISTS idx_ai_feedback_requests_student_assignment")
    op.execute("DROP TABLE IF EXISTS ai_feedback_requests")
