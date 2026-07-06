// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

jest.mock('axios', () => {
  const mockAxios = jest.fn();
  mockAxios.create = jest.fn(() => mockAxios);
  mockAxios.get = jest.fn();
  mockAxios.post = jest.fn();
  mockAxios.put = jest.fn();
  mockAxios.patch = jest.fn();
  mockAxios.delete = jest.fn();
  mockAxios.interceptors = {
    request: { use: jest.fn(), eject: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn() },
  };
  mockAxios.defaults = {};
  return mockAxios;
});

const mockCodemirrorExtension = [];
const mockCodemirrorFacet = { of: jest.fn((value) => value) };
const mockCodemirrorFunction = jest.fn(() => mockCodemirrorExtension);

jest.mock('@codemirror/view', () => {
  class MockEditorView {
    constructor({ state, parent } = {}) {
      this.state = state;
      this.parent = parent;
      this.dispatch = jest.fn();
      this.destroy = jest.fn();
      this.focus = jest.fn();
    }
  }

  MockEditorView.theme = jest.fn(() => mockCodemirrorExtension);
  MockEditorView.updateListener = mockCodemirrorFacet;
  MockEditorView.editable = mockCodemirrorFacet;
  MockEditorView.lineWrapping = mockCodemirrorExtension;

  return {
    EditorView: MockEditorView,
    keymap: mockCodemirrorFacet,
    lineNumbers: mockCodemirrorFunction,
    highlightActiveLineGutter: mockCodemirrorFunction,
    highlightSpecialChars: mockCodemirrorFunction,
    drawSelection: mockCodemirrorFunction,
    dropCursor: mockCodemirrorFunction,
    highlightActiveLine: mockCodemirrorFunction,
  };
});

jest.mock('@codemirror/state', () => {
  class MockCompartment {
    of(value) {
      return value;
    }

    reconfigure(value) {
      return value;
    }
  }

  return {
    EditorState: {
      create: jest.fn((config) => ({
        ...config,
        doc: {
          toString: () => config?.doc || '',
          lines: String(config?.doc || '').split('\n').length,
        },
        selection: {
          main: {
            head: 0,
          },
        },
      })),
      allowMultipleSelections: mockCodemirrorFacet,
      readOnly: mockCodemirrorFacet,
    },
    Compartment: MockCompartment,
  };
});

jest.mock('@codemirror/lang-python', () => ({
  python: mockCodemirrorFunction,
}));

jest.mock('@codemirror/commands', () => ({
  defaultKeymap: [],
  history: mockCodemirrorFunction,
  historyKeymap: [],
  indentWithTab: {},
}));

jest.mock('@codemirror/language', () => ({
  bracketMatching: mockCodemirrorFunction,
  indentOnInput: mockCodemirrorFunction,
  foldGutter: mockCodemirrorFunction,
  foldKeymap: [],
  syntaxHighlighting: mockCodemirrorFunction,
  defaultHighlightStyle: {},
}));

jest.mock('@codemirror/autocomplete', () => ({
  closeBrackets: mockCodemirrorFunction,
  closeBracketsKeymap: [],
  autocompletion: mockCodemirrorFunction,
  completionKeymap: [],
}));

jest.mock('@codemirror/search', () => ({
  searchKeymap: [],
  highlightSelectionMatches: mockCodemirrorFunction,
}));

jest.mock('@codemirror/lint', () => ({
  lintKeymap: [],
}));

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  configurable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
