import IMock from "./common";
import { COURSE, SUCCESS } from "./constant";

const data = COURSE;

IMock(
  "/api/getCourse",
  params => {
    return {
      ...SUCCESS,
      course: data,
    };
  },
  "post"
);
