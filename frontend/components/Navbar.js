"use client";

export default function Navbar({
  models,
  selectedProvider,
  onSelectProvider,
  health,
  onToggleSidebar
}) {
  const isOllamaOnline = health?.llm_providers?.find(p => p.provider === "ollama")?.is_available;

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
        {/* Ollama Local Status Badge */}
        <div className="health-badge">
          <span className={`health-dot ${isOllamaOnline ? "" : "offline"}`}></span>
          <span>
            {isOllamaOnline ? "Ollama Local (Ready)" : "Ollama (Offline)"}
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
          <option value="mock">Offline Test Simulator</option>
        </select>
      </div>
    </header>
  );
}
