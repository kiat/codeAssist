"""Added input logging to database for autograder uploads.

Revision ID: 45b5cf6cc787
Revises: 
Create Date: 2024-04-03 23:10:45.122193

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '45b5cf6cc787'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE test_cases ADD COLUMN IF NOT EXISTS input_data TEXT")

    # Populate initial values here if needed, for example:
    op.execute("UPDATE test_cases SET input_data = '' WHERE input_data IS NULL")

    op.execute("ALTER TABLE test_cases ALTER COLUMN input_data SET NOT NULL")


def downgrade():
    op.execute("ALTER TABLE test_cases DROP COLUMN IF EXISTS input_data")
