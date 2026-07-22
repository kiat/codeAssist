"""Add ai_chat_messages table for student AI conversation memory.

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-06-29 01:00:00.000000

"""
from alembic import op


revision = "b3c4d5e6f7a8"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """CREATE TABLE IF NOT EXISTS ai_chat_messages (
            id VARCHAR PRIMARY KEY,
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            assignment_id UUID NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
            role VARCHAR NOT NULL,
            content TEXT NOT NULL,
            prompt_id VARCHAR,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )"""
    )
    op.execute(
        """CREATE INDEX IF NOT EXISTS idx_ai_chat_messages_student_assignment
           ON ai_chat_messages (student_id, assignment_id)"""
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_ai_chat_messages_student_assignment")
    op.execute("DROP TABLE IF EXISTS ai_chat_messages")
