"""merge container_id and grade publish heads

Revision ID: 51f7b0498833
Revises: a3f92c1e7b04, a3b4c5d6e7f8
Create Date: 2026-10-02 15:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51f7b0498833'
down_revision = ('a3f92c1e7b04', 'a3b4c5d6e7f8')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
