from alembic import op
import sqlalchemy as sa


revision = 'f3a8b2c1d4e5'
down_revision = '92009ca5c92a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('reset_token', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('reset_token_expiry', sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('reset_token_expiry')
        batch_op.drop_column('reset_token')
