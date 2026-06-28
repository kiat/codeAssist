import React, { useRef, useEffect, useState } from "react";
import { Button, Space, Tag, Tooltip } from "antd";
import {
  SaveOutlined,
  PlayCircleOutlined,
  CloudUploadOutlined,
  HistoryOutlined,
  CodeOutlined,
  CheckCircleFilled,
  ClockCircleOutlined,
  CaretRightOutlined,
} from "@ant-design/icons";

// CodeMirror 6 imports
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightSpecialChars, drawSelection, dropCursor, highlightActiveLine } from "@codemirror/view";
import { EditorState, Compartment } from "@codemirror/state";
import { python } from "@codemirror/lang-python";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { bracketMatching, indentOnInput, foldGutter, foldKeymap, syntaxHighlighting, defaultHighlightStyle } from "@codemirror/language";
import { closeBrackets, closeBracketsKeymap, autocompletion, completionKeymap } from "@codemirror/autocomplete";
import { searchKeymap, highlightSelectionMatches } from "@codemirror/search";
import { lintKeymap } from "@codemirror/lint";

// One Dark theme for syntax highlighting
const oneDarkTheme = EditorView.theme({
  "&": {
    color: "#abb2bf",
    backgroundColor: "#282c34",
  },
  ".cm-content": {
    caretColor: "#528bff",
    fontFamily: "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace",
    fontSize: "13px",
    lineHeight: "20px",
  },
  ".cm-cursor, .cm-dropCursor": {
    borderLeftColor: "#528bff",
  },
  "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection": {
    backgroundColor: "#3e4451",
  },
  ".cm-panels": { backgroundColor: "#21252b", color: "#abb2bf" },
  ".cm-panels.cm-panels-top": { borderBottom: "2px solid black" },
  ".cm-panels.cm-panels-bottom": { borderTop: "2px solid black" },
  ".cm-searchMatch": {
    backgroundColor: "#72a1ff59",
    outline: "1px solid #457dff",
  },
  ".cm-searchMatch.cm-searchMatch-selected": {
    backgroundColor: "#6199ff2f",
  },
  ".cm-activeLine": { backgroundColor: "#2c313a" },
  ".cm-selectionMatch": { backgroundColor: "#3e445169" },
  "&.cm-focused .cm-matchingBracket, &.cm-focused .cm-nonmatchingBracket": {
    backgroundColor: "#3e4451",
    outline: "1px solid #528bff",
  },
  ".cm-gutters": {
    backgroundColor: "#282c34",
    color: "#636d83",
    border: "none",
    borderRight: "1px solid #181a1f",
    minWidth: "48px",
  },
  ".cm-activeLineGutter": {
    backgroundColor: "#2c313a",
    color: "#abb2bf",
  },
  ".cm-foldPlaceholder": {
    backgroundColor: "transparent",
    border: "none",
    color: "#528bff",
  },
  ".cm-tooltip": {
    border: "none",
    backgroundColor: "#353b45",
  },
  ".cm-tooltip .cm-tooltip-arrow:before": {
    borderTopColor: "transparent",
    borderBottomColor: "transparent",
  },
  ".cm-tooltip .cm-tooltip-arrow:after": {
    borderTopColor: "#353b45",
    borderBottomColor: "#353b45",
  },
  ".cm-tooltip-autocomplete": {
    "& > ul > li[aria-selected]": {
      backgroundColor: "#2c313a",
      color: "#abb2bf",
    },
  },
}, { dark: true });

/**
 * CodeEditor component — CodeMirror 6 based editor with syntax highlighting,
 * line numbers, auto-save support, and status indicators.
 *
 * Props:
 *   value           – controlled code string
 *   onChange        – (newValue) => void
 *   onSave          – () => void   (manual save)
 *   onSubmit        – () => void   (submit for grading)
 *   onRun           – () => void   (run code without submitting)
 *   onRequestFeedback – () => void
 *   onOpenHistory   – () => void
 *   autoSaveStatus  – 'idle' | 'saving' | 'saved' | 'error'
 *   fileName        – string
 *   language        – string (e.g. "python")
 *   readOnly        – boolean
 */
export default function CodeEditor({
  value = "",
  onChange,
  onSave,
  onSubmit,
  onRun = () => {},
  onRequestFeedback,
  onOpenHistory,
  autoSaveStatus = "idle",
  fileName = "solution.py",
  language = "python",
  readOnly = false,
}) {
  const editorRef = useRef(null);
  const viewRef = useRef(null);
  const onChangeRef = useRef(onChange);
  const readOnlyCompartmentRef = useRef(new Compartment());
  const [cursorLine, setCursorLine] = useState(1);
  const [lineCount, setLineCount] = useState(1);
  const [charCount, setCharCount] = useState(0);

  // Keep refs up to date
  onChangeRef.current = onChange;

  // Initialize CodeMirror once on mount
  useEffect(() => {
    if (!editorRef.current) return;

    const updateListener = EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        const newValue = update.state.doc.toString();
        onChangeRef.current(newValue);
        const lines = newValue.split("\n");
        setLineCount(lines.length);
        setCharCount(newValue.length);
        const pos = update.state.selection.main.head;
        const textBefore = newValue.substring(0, pos);
        const line = textBefore.split("\n").length;
        setCursorLine(line);
      }
      if (update.selectionSet) {
        const pos = update.state.selection.main.head;
        const textBefore = update.state.doc.toString().substring(0, pos);
        const line = textBefore.split("\n").length;
        setCursorLine(line);
      }
    });

    const state = EditorState.create({
      doc: value,
      extensions: [
        lineNumbers(),
        highlightActiveLineGutter(),
        highlightSpecialChars(),
        history(),
        foldGutter(),
        drawSelection(),
        dropCursor(),
        EditorState.allowMultipleSelections.of(true),
        indentOnInput(),
        syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
        bracketMatching(),
        closeBrackets(),
        autocompletion(),
        highlightActiveLine(),
        highlightSelectionMatches(),
        keymap.of([
          ...closeBracketsKeymap,
          ...defaultKeymap,
          ...searchKeymap,
          ...historyKeymap,
          ...foldKeymap,
          ...completionKeymap,
          ...lintKeymap,
          indentWithTab,
        ]),
        python(),
        oneDarkTheme,
        updateListener,
        EditorView.lineWrapping,
        readOnlyCompartmentRef.current.of(
          readOnly
            ? [EditorState.readOnly.of(true), EditorView.editable.of(false)]
            : []
        ),
      ],
    });

    const view = new EditorView({
      state,
      parent: editorRef.current,
    });

    viewRef.current = view;

    const lines = value.split("\n");
    setLineCount(lines.length);
    setCharCount(value.length);

    return () => {
      view.destroy();
      viewRef.current = null;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Toggle readOnly without recreating the editor
  useEffect(() => {
    const view = viewRef.current;
    if (!view) return;
    view.dispatch({
      effects: readOnlyCompartmentRef.current.reconfigure(
        readOnly
          ? [EditorState.readOnly.of(true), EditorView.editable.of(false)]
          : []
      ),
    });
  }, [readOnly]);

  // Sync external value changes into CodeMirror (e.g. version restore)
  useEffect(() => {
    const view = viewRef.current;
    if (!view) return;
    const currentDoc = view.state.doc.toString();
    if (currentDoc !== value) {
      view.dispatch({
        changes: { from: 0, to: currentDoc.length, insert: value },
      });
    }
  }, [value]);

  // Auto-save status indicator
  const renderSaveStatus = () => {
    switch (autoSaveStatus) {
      case "saving":
        return (
          <Tag icon={<ClockCircleOutlined />} color="processing">
            Saving...
          </Tag>
        );
      case "saved":
        return (
          <Tag icon={<CheckCircleFilled />} color="success">
            Saved
          </Tag>
        );
      case "error":
        return <Tag color="error">Save failed</Tag>;
      default:
        return (
          <Tag icon={<ClockCircleOutlined />} color="default">
            Unsaved changes
          </Tag>
        );
    }
  };

  return (
    <div style={styles.container}>
      {/* Toolbar */}
      <div style={styles.toolbar}>
        <div style={styles.toolbarLeft}>
          <Space size="small">
            <CodeOutlined style={{ color: "#1890ff" }} />
            <span style={styles.fileName}>{fileName}</span>
            <Tag color="blue" style={{ marginLeft: 4 }}>
              {language.toUpperCase()}
            </Tag>
          </Space>
        </div>
        <div style={styles.toolbarRight}>
          <Space size="small">
            {renderSaveStatus()}
            <Tooltip title="Save draft (Ctrl+S)">
              <Button
                size="small"
                icon={<SaveOutlined />}
                onClick={onSave}
                disabled={readOnly}
              >
                Save
              </Button>
            </Tooltip>
            <Tooltip title="View version history">
              <Button size="small" icon={<HistoryOutlined />} onClick={onOpenHistory}>
                History
              </Button>
            </Tooltip>
            <Tooltip title="Run your code">
              <Button
                size="small"
                icon={<CaretRightOutlined />}
                onClick={onRun}
                disabled={readOnly}
              >
                Run
              </Button>
            </Tooltip>
            <Tooltip title="Ask AI for feedback on your code">
              <Button
                size="small"
                type="primary"
                ghost
                icon={<PlayCircleOutlined />}
                onClick={onRequestFeedback}
              >
                Get Feedback
              </Button>
            </Tooltip>
            <Button
              size="small"
              type="primary"
              icon={<CloudUploadOutlined />}
              onClick={onSubmit}
              disabled={readOnly}
            >
              Submit for Grading
            </Button>
          </Space>
        </div>
      </div>

      {/* CodeMirror editor container */}
      <div ref={editorRef} style={styles.editorContainer} />

      {/* Status bar */}
      <div style={styles.statusBar}>
        <span>
          Line {lineCount > 0 ? cursorLine : 1}, Col{" "}
          {(() => {
            const lines = (value || "").split("\n");
            const line = lines[cursorLine - 1] || "";
            return line.length;
          })()}
        </span>
        <span style={{ marginLeft: "auto" }}>
          {lineCount} lines | {charCount} chars
        </span>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    border: "1px solid #3e4451",
    borderRadius: 6,
    overflow: "hidden",
    backgroundColor: "#282c34",
    height: "100%",
  },
  toolbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "6px 12px",
    borderBottom: "1px solid #3e4451",
    backgroundColor: "#21252b",
    flexShrink: 0,
  },
  toolbarLeft: {
    display: "flex",
    alignItems: "center",
  },
  toolbarRight: {
    display: "flex",
    alignItems: "center",
  },
  fileName: {
    fontWeight: 600,
    fontSize: 13,
    color: "#abb2bf",
  },
  editorContainer: {
    flex: 1,
    overflow: "auto",
  },
  statusBar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "2px 12px",
    borderTop: "1px solid #3e4451",
    backgroundColor: "#21252b",
    fontSize: 11,
    color: "#636d83",
    flexShrink: 0,
  },
};
