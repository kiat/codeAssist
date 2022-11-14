import IMock from "./common";
import { ASSIGNMENTRESULT, SUBMISSIONHISTORY, SUCCESS } from "./constant";

IMock(
  "/api/uploadFile",
  params => {
    return true;
  },
  "post"
);

IMock(
  "/api/getAssignmentResult",
  params => {
    return {
      ...SUCCESS,
      ...ASSIGNMENTRESULT,
    };
  },
  "post"
);

IMock(
  "/api/submissionHistory",
  params => {
    return {
      ...SUCCESS,
      history: SUBMISSIONHISTORY,
    };
  },
  "post"
);
