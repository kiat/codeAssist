"""Add code_drafts table.

Revision ID: a1b2c3d4e5f6
Revises: 92009ca5c92a
Create Date: 2026-06-12 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '92009ca5c92a'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """CREATE TABLE IF NOT EXISTS code_drafts (
            id UUID PRIMARY KEY,
            student_id UUID NOT NULL REFERENCES users(id),
            assignment_id UUID NOT NULL REFERENCES assignments(id),
            content TEXT NOT NULL,
            file_name VARCHAR,
            version_number INTEGER NOT NULL DEFAULT 1,
            saved_at TIMESTAMP WITH TIME ZONE NOT NULL,
            auto_saved BOOLEAN NOT NULL DEFAULT FALSE
        )"""
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_code_drafts_student_id ON code_drafts (student_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_code_drafts_assignment_id ON code_drafts (assignment_id)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_code_drafts_assignment_id")
    op.execute("DROP INDEX IF EXISTS ix_code_drafts_student_id")
    op.execute("DROP TABLE IF EXISTS code_drafts")
