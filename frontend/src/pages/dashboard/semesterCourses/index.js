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

  return (
      <div>
      <h3>{year && semester ? `${semester} ${year}` : null}</h3>
        {semesterInfo?.map((item, index) => (
          <Course key={index} courseInfo={item} />
        ))}
      </div>
  );
}
