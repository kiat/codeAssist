"""Added file_name column to submissions table

Revision ID: d5fac100798b
Revises: 03dd583914d0
Create Date: 2024-04-12 00:41:19.764147

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd5fac100798b'
down_revision = '03dd583914d0'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS file_name VARCHAR(255)")



def downgrade():
    op.execute("ALTER TABLE submissions DROP COLUMN IF EXISTS file_name")

