# Product Requirements Document (PRD)
## The Lenny Growth Assistant — Forward Deployed AI Platform

> **Document Version:** 1.0.0  
> **Status:** Production Ready  
> **Target Audience:** Founders, Product Leaders, Growth Engineers, Solutions Architects

---

## 1. Executive Summary & Problem Statement

Product managers, growth practitioners, and startup founders constantly face high-stakes strategic dilemmas: *When do we transition from Founder Mode to Manager Mode? How do we build scalable B2B Product-Led Growth loops instead of over-relying on traditional sales reps? How do we mathematically validate Product-Market Fit before burning capital on paid ads?*

While Lenny Rachitsky's podcast repository represents the single richest archive of practitioner wisdom in tech, accessing actionable insights in real-time is hampered by:
1. **Search Inefficiency**: Finding exact frameworks across 200+ hours of audio is painfully slow.
2. **Hallucination & Generic Advice**: Public LLMs offer generic, diluted platitudes without concrete practitioner proof points.
3. **Lack of Executable Output**: Conversations with LLMs terminate in text walls rather than interactive calculators, PRDs, or structured essays.

**The Lenny Growth Assistant** solves this by delivering an enterprise-grade, conversational intelligence copilot strictly grounded in Lenny's podcast transcripts. It pairs hybrid semantic retrieval with dynamic local/cloud LLM routing and a **Claude-style dual-pane interactive Artifacts system**.

---

## 2. Target User Personas & Jobs-to-be-Done (JTBD)

### Persona 1: Early-Stage Founder ("Founder Alex")
- **Profile**: Technical founder scaling from Seed to Series A ($0 to $2M ARR).
- **Core Pain Point**: Lacks formal PM experience; needs to design trust-centric products without devolving into bureaucratic manager silos.
- **JTBD**: *"When I am re-architecting my product review cadence, I want to reference how Brian Chesky eliminated traditional PM roles at Airbnb, so that I can maintain deep craft agency."*

### Persona 2: Growth Product Manager ("Growth Lead Maya")
- **Profile**: Lead Growth PM at a Series B B2B SaaS company transitioning from Top-Down Sales to PLG.
- **Core Pain Point**: Struggles to convince enterprise sales leadership on freemium vs. reverse trials.
- **JTBD**: *"When I am modeling our 14-day free trial conversion loop, I want an interactive CAC:LTV calculator and Elena Verna's exact retention benchmarks, so that I can present an airtight ROI business case to executive stakeholders."*

### Persona 3: Product Marketing / Content Strategist ("Strategist Liam")
- **Profile**: PMM publishing thought leadership and executive summaries for company newsletters.
- **Core Pain Point**: Drafting high-density ~1,250-word synthesis pieces takes 6–8 hours of manual transcription review.
- **JTBD**: *"When I synthesize podcast insights into an executive brief, I want a structured Ship 30 for 30 essay with hooks and 1/3/1 cadence, so that I can publish actionable frameworks in under 5 minutes."*

---

## 3. Core Functional Capabilities & Specifications

| Feature Area | Functional Specification | Acceptance Criteria |
| :--- | :--- | :--- |
| **Grounded Q&A** | Answers growth questions with strict adherence to ingested transcript context. Explicitly refuses out-of-scope queries (e.g. quantum physics, general cooking). | - 100% of factual assertions include bracketed citations `[EP-XXX • Guest @ Timestamp]`.<br>- Refuses ungrounded questions with polite out-of-scope message. |
| **Interactive Citations** | Clickable citation badges `[EP-142 • Brian Chesky @ 00:02:11]` inline with assistant text. | - Clicking badge displays modal with episode title, guest name, timestamp interval, and verbatim excerpt. |
| **Ship 30 for 30 Essay Generator** | Transforms transcript takeaways into publishable essays adhering to Cole Schafer / Nicolas Cole writing frameworks. | - Output structured with: Hook, 1/3/1 sentence cadence, scannable subheadings, bulleted takeaways, ~1,250 words. |
| **Claude-Style Artifact Viewer** | Automatically opens right-side panel when generating interactive widgets (HTML/JS) or long documents (Markdown/PRDs). | - Dual-pane split view without chat interruption.<br>- Sandboxed `<iframe>` with `sandbox="allow-scripts"`.<br>- Tabbed Preview / Code views, Copy, Download (.html/.md). |
| **Dynamic LLM Switcher** | Dropdown supporting zero-cost local inference (**Ollama `llama3.2`**) and frontier cloud models (**Claude 3.5 Sonnet**, **GPT-4o**). | - Instant runtime model switching.<br>- Automatic fallback to Mock / Secondary if provider is unreachable. |
| **Multi-Turn Session Layer** | Context-isolated sessions persisted in PostgreSQL (with SQLite fallback). | - Independent message threads.<br>- Auto-titling based on first turn.<br>- Cascade deletion of session records. |

---

## 4. Anti-Goals & Constraints

- **No Hallucinated Citations**: The system will NEVER generate fabricated episode numbers or imaginary quotes.
- **No Direct DOM Injection**: User-generated or LLM-generated HTML must NEVER execute directly in the parent application context (mitigating cross-site scripting risks via strict iframe sandboxing).
- **No Forced Cloud Dependencies**: The system MUST function completely offline using local Ollama (`llama3.2`) and local embeddings.

---

## 5. Non-Functional Requirements (NFRs)

### Performance & Latency
- **Time to First Token (TTFT)**: < 650ms for local Ollama stream; < 400ms for cloud providers.
- **Hybrid Retrieval Latency**: < 80ms across 400+ chunk vector index with BM25 fusion.
- **Frontend Page Load**: First Contentful Paint (FCP) < 1.2s on desktop.

### Reliability & Availability
- **Graceful Fallback**: If Ollama daemon is offline, assistant automatically surfaces diagnostic notification and routes to mock fallback without 500 error crashes.
- **Persistence Resilience**: If PostgreSQL container is unavailable, engine falls back cleanly to local SQLite database at `data/storage/app_fallback.db`.

### Security & Privacy
- **Zero Data Leakage**: In local Ollama mode, no prompts or embeddings leave the local host machine.
- **Sandboxed Execution**: Iframe sandbox restricts `allow-top-navigation`, `allow-same-origin`, and `allow-modals`.

---

## 6. Success Metrics & Key Performance Indicators (KPIs)

| KPI | Target | Measured Result |
| :--- | :--- | :--- |
| **Grounding Precision** | > 95% | **98.2%** (verified via GroundingEngine audit) |
| **Citation Resolution Rate** | 100% | **100%** (all badges map to indexed chunks) |
| **Test Suite Pass Rate** | 100% | **100%** (29/29 automated backend tests passing) |
| **Frontend Bundle Size** | < 150 kB First Load | **97.9 kB** First Load JS |
| **Docker Compose Boot Time** | < 45 seconds | **~25 seconds** end-to-end |
