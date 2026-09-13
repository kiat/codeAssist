import moment from "moment";

export const formatDayTimeEn = text => {
  return moment(text).format("MMM DD [at] h:mmA");
};

// Shared by the Review Grades SCORE column and the Statistics modal's stat
// tiles so a score's percentage is always computed the same way in both
// places. Returns null when there's no reliable max to divide by.
export const scorePercent = (value, maxPoints) => {
  if (value == null || !maxPoints) return null;
  return Math.round((value / maxPoints) * 100);
};
