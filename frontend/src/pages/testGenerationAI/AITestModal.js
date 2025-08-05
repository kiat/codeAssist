import { useState, useRef } from "react";

export default function AITestModal({ open, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [size, setSize] = useState({ width: 300, height: 200 });

  const isDragging = useRef(false);
  const lastPosition = useRef({ x: 0, y: 0 });

  if (!open) return null;

  const handleSend = async () => {
  if (!input.trim()) return;

  const userMsg = input.trim();
  setMessages((prev) => [...prev, `🧑 You: ${userMsg}`, "🧠 AI is thinking..."]);
  setInput("");

  try {
    const res = await fetch("http://localhost:5002/generate-test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: userMsg }),
    });

    const data = await res.json();
    console.log("AI response data:", data); // ✅ useful for debugging

    const aiResponse = data.output || data.response || "⚠️ No valid response from model";

    // Replace "🧠 AI is thinking..." with actual AI response
    setMessages((prev) => [
      ...prev.slice(0, -1),
      `🤖 AI: ${aiResponse}`,
    ]);
  } catch (error) {
    console.error("Error calling /generate-test:", error);
    setMessages((prev) => [
      ...prev.slice(0, -1),
      "❌ Error: Failed to get response from AI.",
    ]);
  }
};



  const startDrag = (e) => {
    isDragging.current = true;
    lastPosition.current = { x: e.clientX, y: e.clientY };
    document.addEventListener("mousemove", onDrag);
    document.addEventListener("mouseup", stopDrag);
  };

  const onDrag = (e) => {
    if (!isDragging.current) return;

    const dx = lastPosition.current.x - e.clientX;
    const dy = e.clientY - lastPosition.current.y;

    setSize((prev) => ({
      width: Math.max(200, prev.width + dx),
      height: Math.max(150, prev.height + dy),
    }));

    lastPosition.current = { x: e.clientX, y: e.clientY };
  };

  const stopDrag = () => {
    isDragging.current = false;
    document.removeEventListener("mousemove", onDrag);
    document.removeEventListener("mouseup", stopDrag);
  };

  return (
    <div
      style={{
        position: "fixed",
        top: "150px",
        right: "20px",
        background: "linear-gradient(135deg, #4f46e5, #ec4899)",
        backdropFilter: "blur(4px)",
        width: `${size.width}px`,
        height: `${size.height}px`,
        opacity: 0.9,
        zIndex: 9999,
        borderRadius: "8px",
        boxShadow: "0 0 10px rgba(0, 0, 0, 0.3)",
        display: "flex",
        flexDirection: "column",
        padding: "10px",
        boxSizing: "border-box",
        minWidth: "200px",
        minHeight: "150px",
        overflow: "hidden",
      }}
    >
      {/* Close Button */}
      <button
        onClick={onClose}
        style={{
          position: "absolute",
          top: "6px",
          right: "8px",
          background: "transparent",
          border: "none",
          color: "white",
          fontSize: "16px",
          cursor: "pointer",
        }}
        title="Close"
      >
        ╳
      </button>

      {/* Title */}
      <div style={{ fontWeight: "bold", fontSize: "16px", color: "white", marginBottom: "8px" }}>🤖 AI Test Generation</div>

      {/* Chat messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          backgroundColor: "rgba(255, 255, 255, 0.2)",
          padding: "5px",
          borderRadius: "4px",
          marginBottom: "8px",
          color: "white",
          fontSize: "14px",
        }}
      >
        {messages.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: "4px" }}>
            • {msg}
          </div>
        ))}
      </div>

      {/* Input + Send */}
      <div style={{ display: "flex", gap: "4px" }}>
        <input
          type="text"
          value={input}
          placeholder="Enter your assignment specs here to generate test cases"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          style={{
            flex: 1,
            padding: "4px 8px",
            borderRadius: "4px",
            border: "none",
            fontSize: "14px",
          }}
        />
        <button
          onClick={handleSend}
          style={{
            backgroundColor: "white",
            color: "red",
            border: "none",
            borderRadius: "4px",
            padding: "4px 10px",
            fontWeight: "bold",
            cursor: "pointer",
          }}
        >
          Send
        </button>
      </div>

      {/* Custom resize handle on bottom-left */}
      <div
        onMouseDown={startDrag}
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: "10px",
          height: "10px",
          cursor: "nwse-resize",
          backgroundColor: "white",
          borderTopRightRadius: "6px",
        }}
        title="Resize"
      ></div>
    </div>
  );
}
