"""Add ollama_base_url to courses.

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('courses', sa.Column('ollama_base_url', sa.String(), server_default=''))
    op.execute("UPDATE courses SET ollama_base_url = '' WHERE ollama_base_url = 'http://host.docker.internal:11434'")


def downgrade():
    op.drop_column('courses', 'ollama_base_url')
