"""merge migration heads

Two migrations (code-drafts and AI-settings) were branched independently
off the same parent and ended up with separate heads. This merge migration
reconciles them into a single history so `flask db upgrade` has one head
to apply. To avoid a repeat, always run `flask db heads` before starting a
new migration and branch off the current head.

Revision ID: 1bdb41066778
Revises: d4e5f6a7b8c9, f7a8b9c0d1e2
Create Date: 2026-07-06 01:18:47.797757

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1bdb41066778'
down_revision = ('d4e5f6a7b8c9', 'f7a8b9c0d1e2')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
