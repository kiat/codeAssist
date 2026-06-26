"""Add AI settings fields.

Revision ID: a1b2c3d4e5f6
Revises: e1f2a3b4c5d6
Create Date: 2026-06-18 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS default_ai_provider VARCHAR DEFAULT 'openai'")
    op.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS default_ai_model VARCHAR DEFAULT 'gpt-4o-mini'")
    op.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS openai_api_key VARCHAR DEFAULT ''")
    op.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS gemini_api_key VARCHAR DEFAULT ''")
    op.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS claude_api_key VARCHAR DEFAULT ''")
    op.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS default_feedback_style VARCHAR DEFAULT 'hint-based'")
    op.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS default_ai_temperature FLOAT DEFAULT 0.5")

    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_enabled BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS use_course_ai_default BOOLEAN DEFAULT TRUE")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_provider VARCHAR")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_model VARCHAR")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_prompt TEXT")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_temperature FLOAT")
    op.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS ai_feedback_style VARCHAR")


def downgrade():
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_style")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_temperature")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_prompt")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_model")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_provider")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS use_course_ai_default")
    op.execute("ALTER TABLE assignments DROP COLUMN IF EXISTS ai_feedback_enabled")

    op.execute("ALTER TABLE courses DROP COLUMN IF EXISTS default_ai_temperature")
    op.execute("ALTER TABLE courses DROP COLUMN IF EXISTS default_feedback_style")
    op.execute("ALTER TABLE courses DROP COLUMN IF EXISTS claude_api_key")
    op.execute("ALTER TABLE courses DROP COLUMN IF EXISTS gemini_api_key")
    op.execute("ALTER TABLE courses DROP COLUMN IF EXISTS openai_api_key")
    op.execute("ALTER TABLE courses DROP COLUMN IF EXISTS default_ai_model")
    op.execute("ALTER TABLE courses DROP COLUMN IF EXISTS default_ai_provider")
