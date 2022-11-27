import { useCallback } from "react";
import { useState } from "react";
import GradingDashboard from "./GradingDashboard";
import Question from "./Question";

export default () => {
  const [showPageOne, setShowPageOne] = useState(true);

  const changePage = useCallback(() => {
    setShowPageOne(t => !t);
  }, []);

  return (
    <>
      {showPageOne ? (
        <GradingDashboard changePage={changePage} />
      ) : (
        <Question changePage={changePage} />
      )}
    </>
  );
};
