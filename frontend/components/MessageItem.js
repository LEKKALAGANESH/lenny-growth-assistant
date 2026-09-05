"use client";

export default function MessageItem({ message, onSelectCitation, onOpenArtifact }) {
  const isUser = message.role === "user";

  // Simple clean markdown formatter for paragraphs, headers, bold, bullets
  const formatContent = (content) => {
    if (!content) return "";
    
    // Split by lines to render structure
    const lines = content.split("\n");
    return lines.map((line, idx) => {
      // Headers
      if (line.startsWith("### ")) {
        return <h4 key={idx} style={{ margin: "14px 0 6px 0", fontSize: "14px", fontWeight: "700", color: "var(--text-primary)" }}>{line.replace("### ", "")}</h4>;
      }
      if (line.startsWith("## ")) {
        return <h3 key={idx} style={{ margin: "16px 0 8px 0", fontSize: "16px", fontWeight: "700", color: "var(--text-primary)" }}>{line.replace("## ", "")}</h3>;
      }
      if (line.startsWith("# ")) {
        return <h2 key={idx} style={{ margin: "18px 0 10px 0", fontSize: "18px", fontWeight: "700", color: "var(--text-primary)" }}>{line.replace("# ", "")}</h2>;
      }
      // Bullet points
      if (line.startsWith("- ") || line.startsWith("* ")) {
        const bulletText = line.substring(2);
        return (
          <li key={idx} style={{ marginLeft: "18px", marginBottom: "4px", color: "var(--text-primary)" }}>
            {renderFormattedInline(bulletText)}
          </li>
        );
      }
      // Blockquotes
      if (line.startsWith("> ")) {
        return (
          <blockquote key={idx} style={{ borderLeft: "3px solid var(--border-color)", paddingLeft: "12px", margin: "8px 0", color: "var(--text-secondary)", fontStyle: "italic" }}>
            {renderFormattedInline(line.replace("> ", ""))}
          </blockquote>
        );
      }
      // Blank lines
      if (!line.trim()) {
        return <div key={idx} style={{ height: "6px" }} />;
      }
      // Standard paragraph
      return (
        <p key={idx} style={{ marginBottom: "6px" }}>
          {renderFormattedInline(line)}
        </p>
      );
    });
  };

  const renderFormattedInline = (text) => {
    // Process bold text **text**
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, pIdx) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={pIdx} style={{ color: "var(--text-primary)", fontWeight: "600" }}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`}>
      <div className={`message-avatar ${isUser ? "user" : "assistant"}`}>
        {isUser ? "U" : "L"}
      </div>

      <div className="message-content">
        <div style={{ wordBreak: "break-word" }}>
          {formatContent(message.content)}
        </div>

        {/* Citations Footer */}
        {message.citations && message.citations.length > 0 && (
          <div className="citation-badges-container">
            <span style={{ fontSize: "11px", color: "var(--text-muted)", alignSelf: "center", fontWeight: "600", marginRight: "4px", textTransform: "uppercase", letterSpacing: "0.3px" }}>
              Sources:
            </span>
            {message.citations.map((cit, cIdx) => (
              <button
                key={cIdx}
                className="citation-chip"
                onClick={() => onSelectCitation(cit)}
                title="Click to inspect transcript excerpt"
              >
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="16" x2="12" y2="12"></line>
                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                <span>{cit.badge || `Source [${cIdx + 1}]`}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
