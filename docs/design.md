# Design Spec — The Lenny Growth Assistant

Frontend: `frontend/app/page.js` (layout composition), `frontend/app/globals.css` (layout rules),
`frontend/components/{Sidebar,Navbar,ChatPane,ArtifactViewer,CitationModal}.js`.

## 1. Layout: Dual-Pane Split

Three-region desktop layout, composed in `page.js` and styled in `globals.css`:

```
┌─────────────┬──────────────────────────────────────────────┐
│             │  Navbar (56px) — provider dropdown, status    │
│  Sidebar    ├──────────────────────┬───────────────────────┤
│  (280px)    │                      │                       │
│  session    │     Chat Pane        │   Artifact Pane       │
│  history    │     (flex: 1)        │   (opens on demand)   │
│             │                      │                       │
└─────────────┴──────────────────────┴───────────────────────┘
```

- `.app-container`: `display:flex; height:100vh; width:100vw` — the root splits into `.sidebar` (fixed 280px) and `.main-workspace` (`flex:1`).
- `.main-workspace`: column flex — `.navbar` (fixed 56px) stacked above `.split-view-container` (`height: calc(100vh - 56px)`).
- `.split-view-container`: row flex holding `.chat-pane` and, conditionally, the artifact pane (`ArtifactViewer.js`, class `.artifact-pane`).

**The split is binary, not resizable.** There's no drag-to-resize handle — the chat pane is either full-width or shares the row 50/50 with the artifact pane, driven by one CSS class:

```css
.chat-pane { flex: 1; transition: all 0.2s ease; }
.chat-pane.shrunk { max-width: 50%; }
```

`ChatPane.js` toggles `.shrunk` directly off the `isArtifactOpen` boolean passed from `page.js` (`!!activeArtifact`). The `0.2s ease` transition animates the width change; no other pane-open/close animation exists (no slide-in, no fade).

## 2. State Transitions

All state lives in `page.js` (no global store) and cascades down as props — there's no separate design-state layer:

| Trigger | State change | Visual effect |
|---|---|---|
| App loads | `fetchHealth`/`fetchModels`/`fetchSessions` fire in parallel (`Promise.allSettled`); most recent session auto-loads | Sidebar populates; navbar shows health badge + default provider |
| Assistant reply contains `<<<ARTIFACT ...>>>` | `activeArtifact` is set mid-stream, as soon as the opening+closing delimiters are seen in the accumulating buffer (regex match against `accumulatedText`, not the full display text) | Artifact pane mounts, chat pane gets `.shrunk` — this can happen *before* the stream finishes, so the artifact can appear while tokens are still arriving |
| User clicks "×" on the artifact pane | `activeArtifact = null` | Artifact pane unmounts, chat pane returns to full width |
| Stream completes | `loadSession()` re-fetches the persisted session (messages + citations + artifacts) from the backend, replacing the optimistic/streamed state with the DB's version | Any Ship 30 word-count notice appended server-side (see `ship30_essay.py::validate_word_count`) becomes visible here — it wasn't part of the live stream |
| Backend served the response from a different provider than selected (fallback fired) | `page.js`'s `onComplete` handler calls `setSelectedProvider(completion.provider)` | Navbar dropdown and status badge switch to the actual serving provider automatically |
| Citation badge clicked | `activeCitation` is set | `CitationModal` opens as an overlay (not part of the split — it's a modal, independent of the two-pane layout) |
| Sidebar toggle (hamburger) | `isSidebarOpen` flips | Sidebar width/visibility transitions per `.sidebar` styles; does not affect the chat/artifact split |

## 3. Artifact Pane Internals (`ArtifactViewer.js`)

- Two tabs: **Preview** (rendered) and **Code** (raw). Tab state is local to the component (`useState`), reset on remount (i.e., switching artifacts always reopens on "Preview").
- HTML artifacts render inside `<iframe sandbox="allow-scripts" srcDoc={artifact.content}>` — `allow-same-origin` is deliberately omitted (see `docs/architecture.md` §Security). Non-HTML artifacts (markdown/text) render as plain preformatted text, never through the iframe.
- Copy-to-clipboard and download-as-file actions operate on the raw `artifact.content` string directly — no sanitization step currently exists before either the iframe render or the file download (tracked as a pending gap: DOMPurify is specified but not yet wired in).

## 4. Responsive Behavior — current state

**Honest gap, not a design choice:** `globals.css` has zero `@media` queries. The layout is fixed-desktop:
- `.sidebar` is a hardcoded `280px` at every viewport width — it never collapses to an overlay or hides on narrow screens.
- `.app-container` uses `100vw`/`100vh`, so on a narrow viewport the three-column layout compresses each column rather than reflowing to a stacked/mobile layout.
- The chat/artifact 50/50 split (`.chat-pane.shrunk { max-width: 50% }`) has no narrow-viewport override, so on a small screen both panes become too narrow to use rather than one taking priority.

This is a real, unaddressed gap against typical responsive-design expectations — flagged here rather than described as supported, since none of the CSS backs it up. Any future work here should add breakpoints that (a) collapse the sidebar into a toggleable overlay below some width, and (b) make the artifact pane replace (not share) the chat pane below some width, rather than both shrinking simultaneously.
