"use client";

export default function Sidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  isOpen
}) {
  if (!isOpen) return null;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--accent-primary)" }}>
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <span>Sessions</span>
        </div>
      </div>

      <button className="new-chat-btn" onClick={onNewChat}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        <span>New Conversation</span>
      </button>

      <div className="session-list">
        {sessions.length === 0 ? (
          <div style={{ padding: "16px", color: "var(--text-muted)", fontSize: "12px", textAlign: "center" }}>
            No previous conversations.
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={`session-item ${session.id === currentSessionId ? "active" : ""}`}
              onClick={() => onSelectSession(session.id)}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "2px", overflow: "hidden" }}>
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {session.title || "New Chat"}
                </span>
                <span style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>
                  {session.message_count || 0} messages • {session.llm_provider || "ollama"}
                </span>
              </div>

              <button
                className="session-item-delete"
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm("Delete this session?")) {
                    onDeleteSession(session.id);
                  }
                }}
                title="Delete Session"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
