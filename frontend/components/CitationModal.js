"use client";

export default function CitationModal({ citation, onClose }) {
  if (!citation) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span className="artifact-badge" style={{ fontSize: "11px" }}>
              {citation.episode_id?.toUpperCase()}
            </span>
            <h3 style={{ fontSize: "15px", fontWeight: "700", color: "var(--text-primary)" }}>
              {citation.episode_title}
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "16px", padding: "4px" }}
          >
            ✕
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "14px", background: "var(--bg-secondary)", padding: "10px 12px", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
          <div>
            <div style={{ fontSize: "10.5px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "600" }}>Guest</div>
            <div style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-primary)" }}>{citation.guest}</div>
          </div>
          <div>
            <div style={{ fontSize: "10.5px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "600" }}>Timestamp</div>
            <div style={{ fontSize: "13px", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
              {citation.timestamp_start} - {citation.timestamp_end}
            </div>
          </div>
        </div>

        <div style={{ marginBottom: "14px" }}>
          <div style={{ fontSize: "10.5px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "600", marginBottom: "6px" }}>
            Transcript Evidence
          </div>
          <blockquote style={{
            background: "var(--bg-secondary)",
            borderLeft: "3px solid var(--border-focus)",
            padding: "12px 14px",
            borderRadius: "0 6px 6px 0",
            fontSize: "13px",
            lineHeight: "1.6",
            color: "var(--text-secondary)",
            fontStyle: "italic"
          }}>
            "{citation.quote_snippet || citation.quote || citation.metadata?.header}"
          </blockquote>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "14px" }}>
          <button
            onClick={onClose}
            style={{
              padding: "7px 14px",
              background: "var(--bg-secondary)",
              border: "1px solid var(--border-color)",
              color: "var(--text-primary)",
              borderRadius: "6px",
              fontSize: "12.5px",
              fontWeight: "600",
              cursor: "pointer"
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
