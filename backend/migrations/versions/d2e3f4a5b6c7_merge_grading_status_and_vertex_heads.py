"""merge grading-status and Vertex heads

Async grading (4e1c7a9d2b60, PR #400) and the Gemini Vertex migrations
(a7b8c9d0e1f2 -> c1d2e3f4a5b6, PR #369) both branched off b8c9d0e1f2a3.
A merge migration instead of re-parenting, so a dev database that already
ran 4e1c7a9d2b60 still gets the Vertex columns on its next upgrade.

Revision ID: d2e3f4a5b6c7
Revises: 4e1c7a9d2b60, c1d2e3f4a5b6
Create Date: 2026-11-18 14:00:00.000000

"""


# revision identifiers, used by Alembic.
revision = 'd2e3f4a5b6c7'
down_revision = ('4e1c7a9d2b60', 'c1d2e3f4a5b6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
