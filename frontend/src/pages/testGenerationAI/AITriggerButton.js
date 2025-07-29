import { useState } from "react";
import AITestModal from "./AITestModal";

export default function AITriggerButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        style={{
          padding: "8px 16px",
          fontSize: "14px",
          borderRadius: "6px",
          border: "none",
          color: "white",
          cursor: "pointer",
          background: "linear-gradient(270deg, #7c3aed, #ec4899, #7c3aed)",
          backgroundSize: "600% 600%",
          animation: "gradientGlow 4s ease infinite",
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.2)"
        }}
      >
        ✨ Generate test cases with AI
      </button>

      <AITestModal open={open} onClose={() => setOpen(false)} />

      {/* Animation Keyframes */}
      <style>
        {`
          @keyframes gradientGlow {
            0% {
              background-position: 0% 50%;
            }
            50% {
              background-position: 100% 50%;
            }
            100% {
              background-position: 0% 50%;
            }
          }
        `}
      </style>
    </>
  );
}
