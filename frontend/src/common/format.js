import moment from "moment";

export const formatDayTimeEn = text => {
  return moment(text).format("MMM DD [at] h:mmA");
};
