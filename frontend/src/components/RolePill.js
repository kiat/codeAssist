const ROLE_LABELS = { instructor: "Instructor", ta: "TA", student: "Student" };
const ROLE_STYLES = {
  instructor: { background: "#dbeafe", color: "#1e40af" },
  ta:         { background: "#f5f3ff", color: "#5b21b6" },
  student:    { background: "#f3f4f6", color: "#374151" },
};
const PILL = { borderRadius: 999, padding: "3px 10px", fontSize: 13, fontWeight: 500, display: "inline-block" };

export default function RolePill({ role }) {
  const key = role?.toLowerCase();
  return (
    <span style={{ ...PILL, ...(ROLE_STYLES[key] ?? ROLE_STYLES.student) }}>
      {ROLE_LABELS[key] ?? role}
    </span>
  );
}
