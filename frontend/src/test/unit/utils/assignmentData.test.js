import { getPasswordRules, normalizeAssignmentForTable } from '../../../utils/assignmentData';

describe('assignmentData helpers', () => {
  it('normalizes assignment payloads for dashboard tables', () => {
    const assignment = {
      id: 'a1',
      name: 'Homework 1',
      published_date: '2025-01-01T00:00:00.000Z',
      due_date: '2025-01-08T00:00:00.000Z',
      published: true,
      submissions: 10,
      graded_count: 4,
      total_students: 20,
      regrades: 1,
    };

    const normalized = normalizeAssignmentForTable(assignment);

    expect(normalized).toMatchObject({
      id: 'a1',
      name: 'Homework 1',
      released: '2025-01-01T00:00:00.000Z',
      due: '2025-01-08T00:00:00.000Z',
      published: true,
      submissions: 10,
      total_students: 20,
      graded: 20,
      regrades: 1,
    });
  });

  it('recomputes percent graded from enrolled student count when the payload is stale', () => {
    const assignment = {
      id: 'a1',
      name: 'Homework 1',
      submissions: 10,
      graded_count: 4,
      total_students: 20,
      graded: 99,
    };

    const normalized = normalizeAssignmentForTable(assignment);

    expect(normalized.graded).toBe(20);
  });

  it('falls back to submission count when enrolled student count is missing', () => {
    const normalized = normalizeAssignmentForTable({
      id: 'a1',
      submissions: 10,
      graded_count: 4,
    });

    expect(normalized.graded).toBe(40);
  });

  it('normalizes backend regrade counts for dashboard tables', () => {
    const normalized = normalizeAssignmentForTable({
      id: 'a1',
      regrade_count: 3,
    });

    expect(normalized.regrades).toBe(3);
  });

  it('returns the same password validation rules used by signup', () => {
    const rules = getPasswordRules();

    expect(rules).toEqual([
      { required: true, message: 'Please enter a password' },
      { min: 6, message: 'Password must be at least 6 characters' },
    ]);
  });
});
