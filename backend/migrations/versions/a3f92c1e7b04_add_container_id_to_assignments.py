"""add container_id to assignments

Revision ID: a3f92c1e7b04
Revises: 1bdb41066778
Create Date: 2026-07-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3f92c1e7b04'
down_revision = '1bdb41066778'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('assignments', sa.Column('container_id', sa.String(), nullable=True))


def downgrade():
    op.drop_column('assignments', 'container_id')