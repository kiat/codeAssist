import React, { useState, useEffect, useContext } from 'react';
import { Tooltip, Button, Collapse } from 'antd';
import { GlobalContext } from '../../App';
import 'antd/dist/antd.css';

const { Panel } = Collapse;

const TestResultsDisplay = ({ viewMode, studentId, assignmentName, studentName, score, totalPoints, assignmentId, data }) => {
  const { userInfo } = useContext(GlobalContext);
  const [studentCode, setStudentCode] = useState('');
  const [highlightedLines, setHighlightedLines] = useState([]); // Lines to be highlighted
  const [annotations, setAnnotations] = useState([]); // Annotations based on patterns

  // console.log("AI ANNOTATIONS?? ", data["ai_feedback"])

  // let aiAnnotations = data["ai_feedback"]

  const getAiAnnotations = () => {
    if (data && data.ai_feedback) {
      if (typeof data.ai_feedback === 'string') {
        try {
          return JSON.parse(data.ai_feedback);
        } catch (error) {
          console.error('Error parsing ai_feedback:', error);
          return [];
        }
      } else {
        return data.ai_feedback;
      }
    }
    return [];
  };
  // const aiAnnotations = data && data.ai_feedback ? data.ai_feedback : [];

  // console.log("AI ANNOTATIONS?? ", aiAnnotations);

// const aiAnnotations = [
//   { pattern: "class CalculatorException\\(Exception\\):", comment: "Consider adding more detailed documentation for this exception class, specifying under which conditions it is raised, to improve clarity for users of the code." },
//   { pattern: "DIGIT = re.compile\\('\\-?\\d+'\\)", comment: "The regex for `DIGIT` does not account for decimal numbers. Consider updating the pattern to handle floats if needed (e.g., `\\-?\\d+(\\.\\d+)?`)." },
//   { pattern: "TOKEN_CLASSES = \\[DIGIT, WHITESPACE, OPERATOR, PAREN\\]", comment: "This variable `TOKEN_CLASSES` is defined but never used in the code. Consider removing it or utilizing it in `lex` for improved modularity." },
//   { pattern: "raise CalculatorException\\(\"Unknown character\"\\.format\\(string\\[i\\]\\)\\)", comment: "The error message does not include the actual unknown character. Consider updating the message to `\"Unknown character: {}\".format(string[i])` to provide more useful feedback." },
//   { pattern: "while len\\(operator_stack\\) > 0 and \\n                        precedence <= self\\.PRECEDENCES\\[operator_stack\\[-1\\]\\]:", comment: "The `while` loop does not account for parentheses correctly in operator precedence. Consider adding checks for '(' and ')' explicitly to avoid errors." },
//   { pattern: "output\\.append\\(operator_stack\\.pop\\(\\)\\)", comment: "In `parse`, when appending operators from the stack to the output, ensure the stack doesn't contain mismatched parentheses. Add validation for robustness." },
//   { pattern: "elif token == \"\\(\\)\":", comment: "This condition assumes parentheses are balanced. Consider validating the input for unbalanced parentheses before parsing." },
//   { pattern: "if token == '\\+':", comment: "The `eval_rpn` method does not handle division by zero. Add a check to handle this case gracefully." },
//   { pattern: "return input\\('> '\\)", comment: "Using `input` directly in `read` may make it harder to test the `Calculator` class. Consider allowing an optional input source for testing purposes." },
//   { pattern: "while line != \"quit\":", comment: "Consider handling invalid inputs gracefully in the REPL loop, with meaningful error messages instead of crashing the program." },
//   { pattern: "calc\\.loop\\(\\)", comment: "Add a way to handle keyboard interrupts (e.g., `Ctrl+C`) to exit the REPL loop cleanly, avoiding abrupt terminations." },
//   { pattern: "class Calculator\\(object\\):", comment: "Using `object` as a base class is unnecessary in Python 3. You can simply write `class Calculator:`." },
//   { pattern: "WHITESPACE = re.compile\\('\\s+'\\)", comment: "This pattern is redundant as whitespace is skipped in `lex`. Consider removing this regex for simplicity if unused." },
//   { pattern: "output\\.append\\(operator_stack\\.pop\\(\\)\\)", comment: "At the end of `parse`, check for any remaining unmatched parentheses in the `operator_stack` to ensure input validity." },
//   { pattern: "return self\\.D .* \\[tT][oO][kK][eE][nN]\\)", comment: "The `is_digit` and other `is_*` methods directly match tokens without null checks. Consider adding checks to avoid issues with invalid inputs." }
// ];


  // Function to find and highlight lines that match annotation patterns
  const findAnnotations = (code) => {
    const aiAnnotations = getAiAnnotations();
    const lines = code.split('\n');
    const highlighted = [];
    const newAnnotations = [];

    
    aiAnnotations.forEach(({ pattern, comment }) => {
      const regex = new RegExp(pattern);
      lines.forEach((line, index) => {
        if (regex.test(line)) {
          highlighted.push(index + 1); // Store the line number (1-based index)
          newAnnotations.push({ line: index + 1, comment });
        }
      });
    });

    setHighlightedLines(highlighted);
    setAnnotations(newAnnotations);
  };

  useEffect(() => {
    if (data) {
      setStudentCode(data.student_code_file); // Assuming the student code is in this field
      findAnnotations(data.student_code_file); // Find and highlight annotations
    }
  }, [data]);

  const displayCodeWithAnnotations = () => {
    const lines = studentCode.split('\n');
    return (
      <div style={{ maxHeight: '400px', overflowY: 'scroll' }}>
        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
          {lines.map((line, index) => {
            const lineNumber = index + 1;
            const isHighlighted = highlightedLines.includes(lineNumber);
            const annotation = annotations.find(a => a.line === lineNumber);

            return (
              <Tooltip key={lineNumber} title={annotation ? annotation.comment : ''}>
                <div
                  style={{
                    backgroundColor: isHighlighted ? '#ffe6e6' : 'transparent',
                    padding: '2px 0',
                    margin: '2px 0',
                    borderLeft: isHighlighted ? '5px solid red' : 'none',
                  }}
                >
                  {line}
                </div>
              </Tooltip>
            );
          })}
        </pre>
        <Button type="primary" style={{ marginTop: '10px' }}>
          Download
        </Button>
      </div>
    );
  };

  return (
    <div>
      <h2>Submitted Code with Annotations</h2>
      <Collapse accordion>
        <Panel header="Student Code" key="1">
          {displayCodeWithAnnotations()}
        </Panel>
      </Collapse>
    </div>
  );
};

export default TestResultsDisplay;
