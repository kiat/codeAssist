import Course from "./course";

/**
 * Semester modal
 * @param {*} param0
 * @returns
 */
export default function SemesterCourses({
  semesterInfo,
  toggleRelationModalOpen,
  isFirst,
}) {
  const { semester, courses } = semesterInfo;
  return (
    <div
      style={{
        marginBottom: "20px",
      }}
    >
      <h3>{semester}</h3>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
        }}
      >
        {courses?.map(item => (
          <Course key={item.id} courseInfo={item} />
        ))}
        {isFirst ? (
          <div
            style={{
              border: "1px dashed green",
              width: "230px",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              color: "green",
              fontSize: "bold",
              cursor: "pointer",
              height: "125px",
            }}
            onClick={toggleRelationModalOpen}
          >
            + Add a course
          </div>
        ) : null}
      </div>
    </div>
  );
}
