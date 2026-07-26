"""Added submission history and linked submissions.

Revision ID: 03dd583914d0
Revises: 45b5cf6cc787
Create Date: 2024-04-06 03:19:37.915985

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '03dd583914d0'
down_revision = '45b5cf6cc787'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """CREATE TABLE IF NOT EXISTS submission_submitters (
            submission_id UUID NOT NULL REFERENCES submissions(id),
            submitter_id UUID NOT NULL REFERENCES users(id),
            PRIMARY KEY (submission_id, submitter_id)
        )"""
    )
    op.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS submission_number INTEGER")
    op.execute("UPDATE submissions SET submission_number = 1 WHERE submission_number IS NULL")
    op.execute("ALTER TABLE submissions ALTER COLUMN submission_number SET NOT NULL")
    op.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP")
    op.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS active BOOLEAN")
    op.execute("UPDATE submissions SET active = FALSE WHERE active IS NULL")
    op.execute("ALTER TABLE submissions ALTER COLUMN active SET NOT NULL")
    op.execute(
        "ALTER TABLE submissions ALTER COLUMN score TYPE NUMERIC(5, 3) USING score::NUMERIC(5, 3)"
    )
    op.execute("ALTER TABLE submissions DROP COLUMN IF EXISTS executed_at")


def downgrade():
    op.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS executed_at TIMESTAMP")
    op.execute("ALTER TABLE submissions ALTER COLUMN score TYPE DOUBLE PRECISION USING score::DOUBLE PRECISION")
    op.execute("ALTER TABLE submissions DROP COLUMN IF EXISTS active")
    op.execute("ALTER TABLE submissions DROP COLUMN IF EXISTS submitted_at")
    op.execute("ALTER TABLE submissions DROP COLUMN IF EXISTS submission_number")
    op.execute("DROP TABLE IF EXISTS submission_submitters")
