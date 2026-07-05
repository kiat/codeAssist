import { DEFAULT_AI_FEEDBACK_PROMPT } from "./aiFeedback";

export const DEFAULT_AI_ALLOWED_INPUTS = {
  assignment_description: true,
  student_code: true,
  test_results: true,
  test_cases: false,
  student_output: true,
};

export const DEFAULT_AI_FEEDBACK_PROMPTS = [
  {
    id: "check_correctness",
    title: "Check correctness",
    prompt:
      "Check whether the submission appears correct based on the assignment requirements and available test results. Give concise guidance without revealing the full solution.",
    enabled: true,
  },
  {
    id: "debug_failed_tests",
    title: "Debug failed tests",
    prompt:
      "Analyze failed test results and give debugging guidance. Point the student toward likely causes without giving copy-paste fixes.",
    enabled: true,
  },
  {
    id: "review_edge_cases",
    title: "Review edge cases",
    prompt:
      "Review the submission for important edge cases and boundary conditions that may not be fully covered by the visible tests.",
    enabled: true,
  },
  {
    id: "explain_runtime_errors",
    title: "Explain runtime errors",
    prompt:
      "Explain any runtime errors or exceptions in student-friendly language and suggest what part of the code to inspect.",
    enabled: true,
  },
  {
    id: "review_code_style",
    title: "Review code style",
    prompt:
      "Review code organization, readability, and maintainability only when those observations help the student improve the solution safely.",
    enabled: true,
  },
  {
    id: "suggest_algorithmic_improvements",
    title: "Suggest algorithmic improvements",
    prompt:
      "Suggest high-level algorithmic improvements or complexity concerns without rewriting the student's solution.",
    enabled: true,
  },
];

export function normalizeAiAllowedInputs(value = {}) {
  return {
    ...DEFAULT_AI_ALLOWED_INPUTS,
    ...(value || {}),
  };
}

export function normalizeAiFeedbackPrompts(prompts, legacyPrompt) {
  if (Array.isArray(prompts)) {
    return prompts;
  }

  if (legacyPrompt) {
    return [
      {
        id: "legacy_feedback_prompt",
        title: "Custom Feedback",
        prompt: legacyPrompt,
        enabled: true,
      },
    ];
  }

  return DEFAULT_AI_FEEDBACK_PROMPTS;
}

export function createAiFeedbackPrompt() {
  return {
    id: `custom_prompt_${Date.now()}`,
    title: "New Prompt",
    prompt: DEFAULT_AI_FEEDBACK_PROMPT,
    enabled: true,
  };
}
