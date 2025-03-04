import { courseInfo } from "../../createRubric/mock";
import Course from "./course";

export default function SemesterCourses({
  semesterInfo,
  yearInfo,
  courseGroup,
  numCourses
}) {
  const matches = yearInfo.match(/(\d{4})(Spring|Summer|Fall|Winter)/);
  let year = matches && matches[1];
  let semester = matches && matches[2];

  const courseContainerStyle = {
    display: "flex",
    flexDirection: "column", 
    gap: "15px", 
  };

  return (
    <div>
      <h3>{year && semester ? `${semester} ${year}` : null}</h3>
      <div style={courseContainerStyle}>
        {semesterInfo?.map((item, index) => (
          <Course key={index} courseInfo={item} />
        ))}
      </div>
    </div>
  );
}
