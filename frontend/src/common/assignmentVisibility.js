import moment from "moment";

export const isAssignmentVisible = (assignment) => {
  const releaseDate = assignment.published_date
    ? moment(assignment.published_date)
    : null;
  return assignment.published && (!releaseDate || !moment().isBefore(releaseDate));
};

export const getPublishStatus = (assignment) => {
  if (!assignment.published) {
    return "unpublished";
  }

  const releaseDate = assignment.published_date
    ? moment(assignment.published_date)
    : null;
  if (releaseDate && moment().isBefore(releaseDate)) {
    return "scheduled";
  }
  return "published";
};