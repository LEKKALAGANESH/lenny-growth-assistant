"use client";
import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatPane from "@/components/ChatPane";
import ArtifactViewer from "@/components/ArtifactViewer";
import CitationModal from "@/components/CitationModal";
import {
  fetchHealth,
  fetchModels,
  fetchSessions,
  createSession,
  fetchSessionDetails,
  deleteSession,
  streamChatMessage
} from "@/lib/api";

export default function Home() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [streamingMessage, setStreamingMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeArtifact, setActiveArtifact] = useState(null);
  const [activeCitation, setActiveCitation] = useState(null);
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedSkill, setSelectedSkill] = useState("grounded_qa");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [models, setModels] = useState(null);
  const [health, setHealth] = useState(null);

  // Load initial health, models, and sessions
  useEffect(() => {
    async function init() {
      try {
        const [healthData, modelsData, sessionsData] = await Promise.allSettled([
          fetchHealth(),
          fetchModels(),
          fetchSessions()
        ]);

        if (healthData.status === "fulfilled") setHealth(healthData.value);
        if (modelsData.status === "fulfilled") {
          setModels(modelsData.value);
          if (modelsData.value.default_provider) {
            setSelectedProvider(modelsData.value.default_provider);
          }
        }
        if (sessionsData.status === "fulfilled" && sessionsData.value.length > 0) {
          setSessions(sessionsData.value);
          loadSession(sessionsData.value[0].id);
        }
      } catch (err) {
        console.error("Initialization error:", err);
      }
    }
    init();
  }, []);

  const loadSession = async (sessionId) => {
    try {
      const data = await fetchSessionDetails(sessionId);
      setCurrentSessionId(sessionId);
      setMessages(data.messages || []);
      if (data.artifacts && data.artifacts.length > 0) {
        setActiveArtifact(data.artifacts[data.artifacts.length - 1]);
      } else {
        setActiveArtifact(null);
      }
    } catch (err) {
      console.error("Failed to load session:", err);
    }
  };

  const handleNewChat = async () => {
    try {
      const newSession = await createSession("New Chat", selectedProvider);
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      setMessages([]);
      setActiveArtifact(null);
    } catch (err) {
      console.error("Failed to create new chat:", err);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteSession(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);
      if (currentSessionId === sessionId) {
        if (remaining.length > 0) {
          loadSession(remaining[0].id);
        } else {
          setCurrentSessionId(null);
          setMessages([]);
          setActiveArtifact(null);
        }
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  const handleSendMessage = async (userText, skill = selectedSkill) => {
    let targetSessionId = currentSessionId;
    if (!targetSessionId) {
      try {
        const newSession = await createSession(userText.slice(0, 30), selectedProvider);
        setSessions((prev) => [newSession, ...prev]);
        targetSessionId = newSession.id;
        setCurrentSessionId(targetSessionId);
      } catch (e) {
        console.error("Session creation error:", e);
        return;
      }
    }

    // Append user message optimistically
    const userMsg = { role: "user", content: userText, citations: [] };
    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);
    setStreamingMessage("");

    let accumulatedText = "";

    await streamChatMessage(
      targetSessionId,
      userText,
      selectedProvider,
      skill,
      (token) => {
        accumulatedText += token;
        setStreamingMessage((prev) => prev + token);

        // Check if stream started emitting an artifact
        if (accumulatedText.includes("<<<ARTIFACT") && !activeArtifact) {
          const match = accumulatedText.match(/<<<ARTIFACT\s+title=["'](.*?)["'](?:\s+type=["'](.*?)["'])?\s*>>>(.*?)(?:<<<END_ARTIFACT>>>|$)/s);
          if (match) {
            setActiveArtifact({
              title: match[1],
              type: match[2] || "markdown",
              content: match[3]
            });
          }
        }
      },
      async (completion) => {
        // Stream completed: reload session to sync finalized messages and citations
        setIsStreaming(false);
        setStreamingMessage("");

        // Sync the provider selector/status badge to whichever provider actually
        // served the response — the backend auto-routes through its fallback
        // chain server-side, so the dropdown would otherwise keep showing the
        // (possibly now-offline) provider the user originally picked.
        if (completion?.provider && completion.provider !== selectedProvider) {
          setSelectedProvider(completion.provider);
        }
        if (completion?.is_fallback) {
          fetchHealth().then(setHealth).catch(() => {});
        }

        await loadSession(targetSessionId);
        // Refresh session list
        const updatedList = await fetchSessions();
        setSessions(updatedList);
      },
      (error) => {
        console.error("Stream error:", error);
        setIsStreaming(false);
        setStreamingMessage("");
      }
    );
  };

  return (
    <div className="app-container">
      {/* Collapsible Session History Sidebar */}
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={loadSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        isOpen={isSidebarOpen}
      />

      <div className="main-workspace">
        {/* Top Navbar */}
        <Navbar
          models={models}
          selectedProvider={selectedProvider}
          onSelectProvider={setSelectedProvider}
          health={health}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        />

        {/* Split View Container: Left Chat, Right Claude-Style Artifact Viewer */}
        <div className="split-view-container">
          <ChatPane
            messages={messages}
            streamingMessage={streamingMessage}
            isStreaming={isStreaming}
            onSendMessage={handleSendMessage}
            onSelectPrompt={(prompt, skill) => {
              if (skill) setSelectedSkill(skill);
              handleSendMessage(prompt, skill || selectedSkill);
            }}
            onSelectCitation={setActiveCitation}
            selectedSkill={selectedSkill}
            onSelectSkill={setSelectedSkill}
            isArtifactOpen={!!activeArtifact}
          />

          {/* Claude-Style Artifact Viewer Right Pane */}
          {activeArtifact && (
            <ArtifactViewer
              artifact={activeArtifact}
              onClose={() => setActiveArtifact(null)}
            />
          )}
        </div>
      </div>

      {/* Citation Details Inspection Modal */}
      {activeCitation && (
        <CitationModal
          citation={activeCitation}
          onClose={() => setActiveCitation(null)}
        />
      )}
    </div>
  );
}
