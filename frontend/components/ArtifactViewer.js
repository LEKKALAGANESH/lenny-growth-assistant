"use client";
import { useState } from "react";

export default function ArtifactViewer({ artifact, onClose }) {
  const [activeTab, setActiveTab] = useState("preview"); // "preview", "code", "markdown"
  const [copied, setCopied] = useState(false);

  if (!artifact) return null;

  const isHtml = artifact.type === "html" || artifact.content?.includes("<!DOCTYPE html>") || artifact.content?.includes("<html");

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext = isHtml ? "html" : "md";
    const blob = new Blob([artifact.content], { type: isHtml ? "text/html" : "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${artifact.title.toLowerCase().replace(/[^a-z0-9]/g, "_")}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="artifact-pane">
      {/* Header Bar */}
      <div className="artifact-header">
        <div className="artifact-title-group">
          <span className="artifact-badge">{artifact.type || "artifact"}</span>
          <span className="artifact-title">{artifact.title || "Generated Artifact"}</span>
        </div>

        <div className="artifact-actions">
          {/* Tab buttons */}
          <button
            className={`artifact-tab-btn ${activeTab === "preview" ? "active" : ""}`}
            onClick={() => setActiveTab("preview")}
          >
            Preview
          </button>
          <button
            className={`artifact-tab-btn ${activeTab === "code" ? "active" : ""}`}
            onClick={() => setActiveTab("code")}
          >
            Code
          </button>

          <div style={{ width: "1px", height: "18px", background: "var(--border-color)", margin: "0 4px" }} />

          {/* Copy Button */}
          <button className="artifact-action-icon" onClick={handleCopy} title="Copy to clipboard">
            {copied ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            )}
          </button>

          {/* Download Button */}
          <button className="artifact-action-icon" onClick={handleDownload} title="Download Artifact">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
          </button>

          {/* Close Viewer */}
          <button className="artifact-action-icon" onClick={onClose} title="Close Artifact Viewer">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>

      {/* Artifact Content Body */}
      <div className="artifact-body">
        {activeTab === "preview" ? (
          isHtml ? (
            /* Secure isolated iframe sandbox */
            <iframe
              title={artifact.title}
              srcDoc={artifact.content}
              className="artifact-iframe"
              sandbox="allow-scripts"
            />
          ) : (
            <div className="artifact-code-view" style={{ fontFamily: "var(--font-sans)", whiteSpace: "normal" }}>
              <div style={{ maxWidth: "700px", margin: "0 auto", padding: "10px" }}>
                <pre style={{ whiteSpace: "pre-wrap", fontFamily: "var(--font-sans)", fontSize: "14px", lineHeight: "1.7" }}>
                  {artifact.content}
                </pre>
              </div>
            </div>
          )
        ) : (
          /* Raw Code View */
          <div className="artifact-code-view">
            <code>{artifact.content}</code>
          </div>
        )}
      </div>
    </div>
  );
}
