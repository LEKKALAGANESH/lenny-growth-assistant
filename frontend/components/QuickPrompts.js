"use client";
import { STARTER_PROMPTS } from "@/lib/constants";

export default function QuickPrompts({ onSelectPrompt }) {
  return (
    <div className="quick-prompts-container">
      {STARTER_PROMPTS.map((item) => (
        <div
          key={item.id}
          className="quick-prompt-card"
          onClick={() => onSelectPrompt(item.prompt, item.skill)}
        >
          <div className="quick-prompt-title">{item.title}</div>
          <div className="quick-prompt-desc">{item.desc}</div>
        </div>
      ))}
    </div>
  );
}
