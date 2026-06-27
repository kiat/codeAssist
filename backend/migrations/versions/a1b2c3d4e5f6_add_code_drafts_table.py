"""Add code_drafts table.

Revision ID: a1b2c3d4e5f6
Revises: 92009ca5c92a
Create Date: 2026-06-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '92009ca5c92a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('code_drafts',
        sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('student_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('assignment_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('saved_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('auto_saved', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id']),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_code_drafts_student_id', 'code_drafts', ['student_id'])
    op.create_index('ix_code_drafts_assignment_id', 'code_drafts', ['assignment_id'])


def downgrade():
    op.drop_index('ix_code_drafts_assignment_id', table_name='code_drafts')
    op.drop_index('ix_code_drafts_student_id', table_name='code_drafts')
    op.drop_table('code_drafts')
