import { DEFAULT_AI_FEEDBACK_PROMPT } from "./aiFeedback";

export const AI_PROVIDER_KEYS = {
  OPENAI: "openai",
  GEMINI: "gemini",
  GEMINI_VERTEX: "gemini_vertex",
  CLAUDE: "claude",
  OLLAMA: "ollama",
};

export const AI_PROVIDERS = [
  {
    key: AI_PROVIDER_KEYS.OPENAI,
    label: "ChatGPT",
    displayName: "OpenAI / ChatGPT",
  },
  {
    key: AI_PROVIDER_KEYS.GEMINI,
    label: "Gemini",
    displayName: "Google Gemini",
  },
  {
    key: AI_PROVIDER_KEYS.GEMINI_VERTEX,
    label: "Gemini over Vertex AI",
    displayName: "Gemini over Vertex AI",
  },
  {
    key: AI_PROVIDER_KEYS.CLAUDE,
    label: "Claude",
    displayName: "Anthropic Claude",
  },
  {
    key: AI_PROVIDER_KEYS.OLLAMA,
    label: "Ollama",
    displayName: "Ollama (Local LLM)",
  },
];

export const AI_PROVIDER_DEFAULT_MODELS = {
  [AI_PROVIDER_KEYS.OPENAI]: "gpt-4o",
  [AI_PROVIDER_KEYS.GEMINI]: "gemini-1.5-flash",
  [AI_PROVIDER_KEYS.GEMINI_VERTEX]: "gemini-2.5-flash",
  [AI_PROVIDER_KEYS.CLAUDE]: "claude-sonnet-5",
  [AI_PROVIDER_KEYS.OLLAMA]: "llama3",
};

export const VERTEX_LOCATION_OPTIONS = [
  { label: "Server default", value: "" },
  { label: "global", value: "global" },
  { label: "us-central1", value: "us-central1" },
];

export function isVertexProvider(provider) {
  return provider === AI_PROVIDER_KEYS.GEMINI_VERTEX;
}

export function getAiProviderLabel(provider) {
  return (
    AI_PROVIDERS.find((item) => item.key === provider)?.label ||
    provider ||
    "No provider"
  );
}

export function hasProviderConfiguration(course, provider) {
  if (provider === AI_PROVIDER_KEYS.OPENAI) {
    return !!course?.has_openai_api_key;
  }
  if (provider === AI_PROVIDER_KEYS.GEMINI) {
    return !!course?.has_gemini_api_key;
  }
  if (provider === AI_PROVIDER_KEYS.GEMINI_VERTEX) {
    return !!course?.has_gemini_vertex_config;
  }
  if (provider === AI_PROVIDER_KEYS.CLAUDE) {
    return !!course?.has_claude_api_key;
  }
  if (provider === AI_PROVIDER_KEYS.OLLAMA) {
    return !!course?.has_ollama_api_key;
  }
  return false;
}

export const DEFAULT_AI_ALLOWED_INPUTS = {
  assignment_description: true,
  student_code: true,
  test_results: true,
  test_cases: false,
  student_output: true,
  submission_history: true,
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
  {
    id: "check_code_syntax",
    title: "Check code syntax",
    prompt:
      "Review the student's code for syntax errors, Python best practices, and language-specific issues. Point out problematic patterns and suggest what to fix without rewriting the code.",
    enabled: true,
  },
  {
    id: "compare_to_optimal_solution",
    title: "Compare to optimal solution",
    prompt:
      "You are comparing the student's code against an optimal reference solution. First, analyze the assignment description to understand what the problem requires. Then generate an optimal approach internally and compare it to the student's code. Identify algorithmic differences, time/space complexity gaps, and structural improvements. Give feedback on how the student's approach differs from the optimal one without revealing the full reference solution. Focus on algorithmic thinking and design patterns.",
    enabled: true,
  },
  {
    id: "personalized_feedback",
    title: "Personalized feedback",
    prompt:
      "Based on this student's history and current submission, provide personalized feedback. Reference patterns from their previous work where relevant. Focus on areas where this specific student tends to struggle and give targeted guidance. Encourage growth and acknowledge improvements from past submissions.",
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
