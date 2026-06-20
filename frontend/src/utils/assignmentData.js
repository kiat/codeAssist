export const getPasswordRules = ({ required = true } = {}) => [
  {
    validator: (_, value) => {
      // If it's required (Sign Up/Log In) and empty, reject it
      if (required && (!value || value.trim() === "")) {
        return Promise.reject(new Error('Please enter a password'));
      }

      // If it's NOT required (Edit Account) and empty, let it pass
      if (!required && (!value || value.trim() === "")) {
        return Promise.resolve();
      }

      // Centralized minimum length rule
      const minLength = 6; 
      if (value && value.length < minLength) {
        return Promise.reject(new Error(`Password must be at least ${minLength} characters`));
      }

      return Promise.resolve();
    }
  }
];
/*
export const normalizeAssignmentForTable = (assignment = {}) => {
  const submissions = Number(assignment.submissions ?? assignment.submission_count ?? 0) || 0;
  const gradedCount = Number(assignment.graded_count ??   const totalStudents = Number(
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
gnment.regrades ?? 0,
  };
};
*/