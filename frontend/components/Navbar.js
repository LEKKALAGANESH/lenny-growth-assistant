"use client";

export default function Navbar({
  models,
  selectedProvider,
  onSelectProvider,
  health,
  onToggleSidebar
}) {
  const PROVIDER_LABELS = {
    ollama: "Ollama (Local)",
    anthropic: "Anthropic",
    openai: "OpenAI",
    groq: "Groq",
    gemini: "Gemini",
    mock: "Offline Test Simulator"
  };

  const activeStatus = health?.llm_providers?.find(p => p.provider === selectedProvider);
  const isActiveProviderOnline = activeStatus?.is_available ?? true;
  const activeLabel = PROVIDER_LABELS[selectedProvider] || selectedProvider;

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <button
          onClick={onToggleSidebar}
          style={{ background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer", display: "flex", alignItems: "center" }}
          title="Toggle Sidebar"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="9" y1="3" x2="9" y2="21"></line>
          </svg>
        </button>
        <span style={{ fontSize: "15px", fontWeight: "700", color: "var(--text-primary)", letterSpacing: "-0.3px" }}>
          The Lenny Growth Assistant
        </span>
        <span className="navbar-badge">Demo</span>
      </div>

      <div className="navbar-controls">
        {/* Active Provider Status Badge — reflects whichever provider is selected.
            If it's down, the backend auto-cascades through the full fallback chain
            (see llm/manager.py), so the badge is informational, not blocking. */}
        <div className="health-badge" title={activeStatus?.status_message || ""}>
          <span className={`health-dot ${isActiveProviderOnline ? "" : "offline"}`}></span>
          <span>
            {activeLabel} {isActiveProviderOnline ? "(Ready)" : "(Offline — auto-routing to fallback)"}
          </span>
        </div>

        {/* Model Provider Dropdown Switcher */}
        <select
          className="model-selector"
          value={selectedProvider}
          onChange={(e) => onSelectProvider(e.target.value)}
        >
          <option value="ollama">Ollama (Local LLM)</option>
          <option value="anthropic">Anthropic Claude 3.5 Sonnet</option>
          <option value="openai">OpenAI GPT-4o</option>
          <option value="groq">Groq (Fast Inference)</option>
          <option value="gemini">Google Gemini</option>
          <option value="mock">Offline Test Simulator</option>
        </select>
      </div>
    </header>
  );
}
