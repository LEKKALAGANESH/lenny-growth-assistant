"use client";
import { useEffect, useRef } from "react";
import MessageItem from "./MessageItem";
import QuickPrompts from "./QuickPrompts";
import ChatInput from "./ChatInput";

export default function ChatPane({
  messages,
  streamingMessage,
  isStreaming,
  onSendMessage,
  onSelectPrompt,
  onSelectCitation,
  selectedSkill,
  onSelectSkill,
  isArtifactOpen
}) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage]);

  return (
    <main className={`chat-pane ${isArtifactOpen ? "shrunk" : ""}`}>
      <div className="messages-container">
        {messages.length === 0 && !streamingMessage ? (
          <div style={{ margin: "auto", textAlign: "center", width: "100%", maxWidth: "820px" }}>
            <div style={{
              width: "42px",
              height: "42px",
              borderRadius: "10px",
              backgroundColor: "var(--accent-primary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px auto"
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <h2 style={{ fontSize: "20px", fontWeight: "700", marginBottom: "8px", letterSpacing: "-0.4px", color: "var(--text-primary)" }}>
              The Lenny Growth Assistant
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "13.5px", maxWidth: "520px", margin: "0 auto 24px auto", lineHeight: "1.5" }}>
              Grounded product and growth insights from Lenny Rachitsky's podcast interviews with Brian Chesky, Elena Verna, Shreyas Doshi, and Sean Ellis.
            </p>

            <QuickPrompts onSelectPrompt={onSelectPrompt} />
          </div>
        ) : (
          <>
            {messages.map((msg, index) => (
              <MessageItem
                key={index}
                message={msg}
                onSelectCitation={onSelectCitation}
              />
            ))}

            {/* Live Streaming Assistant Turn */}
            {streamingMessage && (
              <MessageItem
                message={{
                  role: "assistant",
                  content: streamingMessage,
                  citations: []
                }}
                onSelectCitation={onSelectCitation}
              />
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <ChatInput
        onSendMessage={onSendMessage}
        isStreaming={isStreaming}
        selectedSkill={selectedSkill}
        onSelectSkill={onSelectSkill}
      />
    </main>
  );
}
