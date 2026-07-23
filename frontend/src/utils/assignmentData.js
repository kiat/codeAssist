export const getPasswordRules = ({ required = true } = {}) => [
  ...(required
    ? [{ required: true, message: 'Please enter a password' }]
    : []),
  { min: 6, message: 'Password must be at least 6 characters' },
];

export const normalizeAssignmentForTable = (assignment = {}) => {
  const submissions = Number(assignment.submissions ?? assignment.submission_count ?? 0) || 0;
  const gradedCount = Number(assignment.graded_count ?? 0) || 0;
  const totalStudents = Number(
    assignment.total_students ?? assignment.enrolled_students ?? assignment.class_size ?? submissions
  ) || 0;
  const gradedPercent = totalStudents > 0
    ? Math.round((gradedCount / totalStudents) * 100)
    : 0;

  return {
    ...assignment,
    name: assignment.name ?? assignment.assignmentName ?? '',
    released: assignment.published_date ?? assignment.released ?? assignment.release_date ?? null,
    due: assignment.due_date ?? assignment.due ?? null,
    published: Boolean(assignment.published),
    submissions,
    total_students: totalStudents,
    graded: gradedPercent,
    regrades: Number(assignment.regrades ?? assignment.regrade_count ?? 0) || 0,
  };
};
