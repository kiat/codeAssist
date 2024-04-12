"""Added file_name column to submissions table

Revision ID: d5fac100798b
Revises: 03dd583914d0
Create Date: 2024-04-12 00:41:19.764147

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5fac100798b'
down_revision = '03dd583914d0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('submissions', sa.Column('file_name', sa.String(length=255), nullable=True))



def downgrade():
    op.drop_column('submissions', 'file_name')

