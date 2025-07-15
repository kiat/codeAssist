"""Fixed score value in DB.

Revision ID: 92009ca5c92a
Revises: d5fac100798b
Create Date: 2024-04-12 03:18:11.586829

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92009ca5c92a'
down_revision = 'd5fac100798b'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('submissions') as batch_op:
        batch_op.alter_column('score',
                              type_=sa.Float(),
                              existing_type=sa.Numeric,
                              existing_nullable=True)

def downgrade():
    with op.batch_alter_table('submissions') as batch_op:
        batch_op.alter_column('score',
                              type_=sa.Numeric,
                              existing_type=sa.Float(),
                              existing_nullable=True)
