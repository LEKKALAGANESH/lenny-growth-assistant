"use client";
import { useState, useRef, useEffect } from "react";

export default function ChatInput({ onSendMessage, isStreaming, selectedSkill, onSelectSkill }) {
  const [input, setInput] = useState("");
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSendMessage(input, selectedSkill);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const skills = [
    { id: "grounded_qa", label: "Grounded Q&A" },
    { id: "ship30_essay", label: "Ship 30 Essay" },
    { id: "artifact", label: "Interactive Artifact" }
  ];

  return (
    <div className="chat-input-wrapper">
      {/* Skill Selector Mode Buttons */}
      <div style={{ maxWidth: "820px", margin: "0 auto 8px auto", display: "flex", gap: "6px", alignItems: "center" }}>
        <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.4px" }}>
          Mode:
        </span>
        {skills.map((skill) => {
          const isSelected = selectedSkill === skill.id;
          return (
            <button
              key={skill.id}
              onClick={() => onSelectSkill(skill.id)}
              style={{
                backgroundColor: isSelected ? "var(--accent-primary)" : "var(--bg-secondary)",
                border: `1px solid ${isSelected ? "var(--accent-primary)" : "var(--border-color)"}`,
                color: isSelected ? "#ffffff" : "var(--text-secondary)",
                padding: "3px 10px",
                borderRadius: "14px",
                fontSize: "11.5px",
                fontWeight: "600",
                cursor: "pointer",
                transition: "all 0.15s ease"
              }}
            >
              {skill.label}
            </button>
          );
        })}
      </div>

      <div className="chat-input-box">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Ask a question about product strategy, growth loops, or frameworks..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={isStreaming}
        />

        <button
          className="chat-send-btn"
          onClick={handleSubmit}
          disabled={!input.trim() || isStreaming}
          title="Send message"
        >
          {isStreaming ? (
            <div style={{ width: "12px", height: "12px", border: "2px solid #ffffff", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          )}
        </button>
      </div>

      <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
