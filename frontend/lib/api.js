const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = `${API_BASE}/api`;

async function request(path, options = {}) {
  const res = await fetch(`${API_PREFIX}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export function fetchHealth() {
  return request("/health");
}

export function fetchModels() {
  return request("/models");
}

export function fetchSessions() {
  return request("/sessions");
}

export function createSession(title, llmProvider) {
  return request("/sessions", {
    method: "POST",
    body: JSON.stringify({ title, llm_provider: llmProvider })
  });
}

export function fetchSessionDetails(sessionId) {
  return request(`/sessions/${sessionId}`);
}

export function deleteSession(sessionId) {
  return request(`/sessions/${sessionId}`, { method: "DELETE" });
}

// Server-Sent Events stream from POST /chat/stream. fetch() is used (not
// EventSource) because EventSource can't send a POST body/JSON payload.
export async function streamChatMessage(sessionId, message, llmProvider, skill, onToken, onComplete, onError) {
  try {
    const res = await fetch(`${API_PREFIX}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        llm_provider: llmProvider,
        skill
      })
    });

    if (!res.ok || !res.body) {
      throw new Error(`API ${res.status}: ${res.statusText}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const rawEvent of events) {
        const lines = rawEvent.split("\n");
        let eventName = "message";
        let data = "";
        for (const line of lines) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          else if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        if (!data) continue;

        const parsed = JSON.parse(data);
        if (eventName === "complete") {
          await onComplete?.(parsed);
        } else if (typeof parsed.token === "string") {
          onToken?.(parsed.token);
        }
      }
    }
  } catch (err) {
    onError?.(err);
  }
}
