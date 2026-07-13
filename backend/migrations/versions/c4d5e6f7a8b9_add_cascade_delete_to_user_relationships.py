"""Add ON DELETE CASCADE to foreign keys referencing users.id.

When a user is deleted, their enrollments, submissions, extensions,
code drafts, and (for instructors) courses and all downstream records
are now automatically removed by the database, preventing orphaned
rows.

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-06-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c4d5e6f7a8b9'
down_revision = '1bdb41066778'
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing foreign key constraints and re-add them with ON DELETE CASCADE.
    # Table: enrollments
    op.drop_constraint('enrollments_student_id_fkey', 'enrollments', type_='foreignkey')
    op.drop_constraint('enrollments_course_id_fkey', 'enrollments', type_='foreignkey')
    op.create_foreign_key('enrollments_student_id_fkey', 'enrollments', 'users', ['student_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('enrollments_course_id_fkey', 'enrollments', 'courses', ['course_id'], ['id'], ondelete='CASCADE')

    # Table: courses — instructor_id uses RESTRICT to prevent accidental deletion
    # of all courses, assignments, and student grades when removing an instructor.
    op.drop_constraint('courses_instructor_id_fkey', 'courses', type_='foreignkey')
    op.create_foreign_key('courses_instructor_id_fkey', 'courses', 'users', ['instructor_id'], ['id'], ondelete='RESTRICT')

    # Table: assignments
    op.drop_constraint('assignments_course_id_fkey', 'assignments', type_='foreignkey')
    op.create_foreign_key('assignments_course_id_fkey', 'assignments', 'courses', ['course_id'], ['id'], ondelete='CASCADE')

    # Table: submissions
    op.drop_constraint('submissions_student_id_fkey', 'submissions', type_='foreignkey')
    op.drop_constraint('submissions_assignment_id_fkey', 'submissions', type_='foreignkey')
    op.create_foreign_key('submissions_student_id_fkey', 'submissions', 'users', ['student_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('submissions_assignment_id_fkey', 'submissions', 'assignments', ['assignment_id'], ['id'], ondelete='CASCADE')

    # Table: submission_submitters
    op.drop_constraint('submission_submitters_submission_id_fkey', 'submission_submitters', type_='foreignkey')
    op.drop_constraint('submission_submitters_submitter_id_fkey', 'submission_submitters', type_='foreignkey')
    op.create_foreign_key('submission_submitters_submission_id_fkey', 'submission_submitters', 'submissions', ['submission_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('submission_submitters_submitter_id_fkey', 'submission_submitters', 'users', ['submitter_id'], ['id'], ondelete='CASCADE')

    # Table: test_cases
    op.drop_constraint('test_cases_assignment_id_fkey', 'test_cases', type_='foreignkey')
    op.create_foreign_key('test_cases_assignment_id_fkey', 'test_cases', 'assignments', ['assignment_id'], ['id'], ondelete='CASCADE')

    # Table: test_case_results
    op.drop_constraint('test_case_results_submission_id_fkey', 'test_case_results', type_='foreignkey')
    op.drop_constraint('test_case_results_test_case_id_fkey', 'test_case_results', type_='foreignkey')
    op.create_foreign_key('test_case_results_submission_id_fkey', 'test_case_results', 'submissions', ['submission_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('test_case_results_test_case_id_fkey', 'test_case_results', 'test_cases', ['test_case_id'], ['id'], ondelete='CASCADE')

    # Table: regrade_requests
    op.drop_constraint('regrade_requests_submission_id_fkey', 'regrade_requests', type_='foreignkey')
    op.create_foreign_key('regrade_requests_submission_id_fkey', 'regrade_requests', 'submissions', ['submission_id'], ['id'], ondelete='CASCADE')

    # Table: assignment_extensions
    op.drop_constraint('assignment_extensions_assignment_id_fkey', 'assignment_extensions', type_='foreignkey')
    op.drop_constraint('assignment_extensions_student_id_fkey', 'assignment_extensions', type_='foreignkey')
    op.create_foreign_key('assignment_extensions_assignment_id_fkey', 'assignment_extensions', 'assignments', ['assignment_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('assignment_extensions_student_id_fkey', 'assignment_extensions', 'users', ['student_id'], ['id'], ondelete='CASCADE')

    # Table: code_drafts
    op.drop_constraint('code_drafts_student_id_fkey', 'code_drafts', type_='foreignkey')
    op.drop_constraint('code_drafts_assignment_id_fkey', 'code_drafts', type_='foreignkey')
    op.create_foreign_key('code_drafts_student_id_fkey', 'code_drafts', 'users', ['student_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('code_drafts_assignment_id_fkey', 'code_drafts', 'assignments', ['assignment_id'], ['id'], ondelete='CASCADE')


def downgrade():
    # Revert foreign keys back to no cascade (RESTRICT / no action)
    # Table: enrollments
    op.drop_constraint('enrollments_student_id_fkey', 'enrollments', type_='foreignkey')
    op.drop_constraint('enrollments_course_id_fkey', 'enrollments', type_='foreignkey')
    op.create_foreign_key('enrollments_student_id_fkey', 'enrollments', 'users', ['student_id'], ['id'])
    op.create_foreign_key('enrollments_course_id_fkey', 'enrollments', 'courses', ['course_id'], ['id'])

    # Table: courses
    op.drop_constraint('courses_instructor_id_fkey', 'courses', type_='foreignkey')
    op.create_foreign_key('courses_instructor_id_fkey', 'courses', 'users', ['instructor_id'], ['id'])

    # Table: assignments
    op.drop_constraint('assignments_course_id_fkey', 'assignments', type_='foreignkey')
    op.create_foreign_key('assignments_course_id_fkey', 'assignments', 'courses', ['course_id'], ['id'])

    # Table: submissions
    op.drop_constraint('submissions_student_id_fkey', 'submissions', type_='foreignkey')
    op.drop_constraint('submissions_assignment_id_fkey', 'submissions', type_='foreignkey')
    op.create_foreign_key('submissions_student_id_fkey', 'submissions', 'users', ['student_id'], ['id'])
    op.create_foreign_key('submissions_assignment_id_fkey', 'submissions', 'assignments', ['assignment_id'], ['id'])

    # Table: submission_submitters
    op.drop_constraint('submission_submitters_submission_id_fkey', 'submission_submitters', type_='foreignkey')
    op.drop_constraint('submission_submitters_submitter_id_fkey', 'submission_submitters', type_='foreignkey')
    op.create_foreign_key('submission_submitters_submission_id_fkey', 'submission_submitters', 'submissions', ['submission_id'], ['id'])
    op.create_foreign_key('submission_submitters_submitter_id_fkey', 'submission_submitters', 'users', ['submitter_id'], ['id'])

    # Table: test_cases
    op.drop_constraint('test_cases_assignment_id_fkey', 'test_cases', type_='foreignkey')
    op.create_foreign_key('test_cases_assignment_id_fkey', 'test_cases', 'assignments', ['assignment_id'], ['id'])

    # Table: test_case_results
    op.drop_constraint('test_case_results_submission_id_fkey', 'test_case_results', type_='foreignkey')
    op.drop_constraint('test_case_results_test_case_id_fkey', 'test_case_results', type_='foreignkey')
    op.create_foreign_key('test_case_results_submission_id_fkey', 'test_case_results', 'submissions', ['submission_id'], ['id'])
    op.create_foreign_key('test_case_results_test_case_id_fkey', 'test_case_results', 'test_cases', ['test_case_id'], ['id'])

    # Table: regrade_requests
    op.drop_constraint('regrade_requests_submission_id_fkey', 'regrade_requests', type_='foreignkey')
    op.create_foreign_key('regrade_requests_submission_id_fkey', 'regrade_requests', 'submissions', ['submission_id'], ['id'])

    # Table: assignment_extensions
    op.drop_constraint('assignment_extensions_assignment_id_fkey', 'assignment_extensions', type_='foreignkey')
    op.drop_constraint('assignment_extensions_student_id_fkey', 'assignment_extensions', type_='foreignkey')
    op.create_foreign_key('assignment_extensions_assignment_id_fkey', 'assignment_extensions', 'assignments', ['assignment_id'], ['id'])
    op.create_foreign_key('assignment_extensions_student_id_fkey', 'assignment_extensions', 'users', ['student_id'], ['id'])

    # Table: code_drafts
    op.drop_constraint('code_drafts_student_id_fkey', 'code_drafts', type_='foreignkey')
    op.drop_constraint('code_drafts_assignment_id_fkey', 'code_drafts', type_='foreignkey')
    op.create_foreign_key('code_drafts_student_id_fkey', 'code_drafts', 'users', ['student_id'], ['id'])
    op.create_foreign_key('code_drafts_assignment_id_fkey', 'code_drafts', 'assignments', ['assignment_id'], ['id'])
