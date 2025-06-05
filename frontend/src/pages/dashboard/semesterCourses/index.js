import Course from "./course";

export default function SemesterCourses({ courses, toggleModal, setSelectedCourse }) {  const semesterContainerStyle = {
    display: "flex",
    flexDirection: "column",
    gap: "30px",
    width: "100%",
    paddingLeft: "30px",
  };

  const semesterHeaderStyle = {
    fontWeight: "bold",
    fontSize: "20px",
    marginBottom: "10px",
  };

  const courseGroupStyle = {
    display: "flex",
    flexWrap: "wrap",
    gap: "20px",
    alignItems: "center",
  };

  const addCourseButtonStyle = {
    border: "1px dashed green",
    width: "230px",
    height: "138px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    color: "green",
    fontWeight: "bold",
    fontSize: "16px",
    cursor: "pointer",
    boxSizing: "border-box",
    flexShrink: 0,
    textAlign: "center",
  };

  const sortedSemesters = Object.keys(courses).sort((a, b) => {
    const regex = /(\d{1,4})(Spring|Summer|Fall|Winter)/;
    const matchA = a.match(regex);
    const matchB = b.match(regex);

        if (!matchA || !matchB) return 0;

        const yearA = parseInt(matchA[1]); 
        const yearB = parseInt(matchB[1]);

        if (yearA !== yearB) {
          return yearB - yearA; 
        }

    const semesterOrder = { Spring: 1, Summer: 2, Fall: 3, Winter: 4 };
    return semesterOrder[matchA[2]] - semesterOrder[matchB[2]];
  });

  return (
    <div style={semesterContainerStyle}>
      {sortedSemesters.length > 0 ? (
        sortedSemesters.map((semesterKey, index) => {
          const regex = /(\d{1,4})(Spring|Summer|Fall|Winter)/;
          const match = semesterKey.match(regex);
          const semester = match ? match[2] : "";
          const year = match ? match[1] : "";
  
          return (
            <div key={semesterKey} style={{ width: "100%" }}>
              <h3 style={semesterHeaderStyle}>{`${semester} ${year}`}</h3>
              <div style={courseGroupStyle}>
                {courses[semesterKey].map((course, index) => (
                    <Course key={course.id} courseInfo={course} setSelectedCourse={setSelectedCourse} />                    
                ))}
                {index === 0 && (
                  <div style={addCourseButtonStyle} onClick={toggleModal}>
                    + Add a course
                  </div>
                )}
              </div>
            </div>
          );
        })
      ) : (
        <div style={addCourseButtonStyle} onClick={toggleModal}>
          + Add a course
        </div>
      )}
    </div>
  );
}
