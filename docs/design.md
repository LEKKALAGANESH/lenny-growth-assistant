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

- `.app-container`: `display:flex; height:100vh; width:100vw` — the root splits into `.sidebar` and `.main-workspace`.
- `.main-workspace`: column flex — `.navbar` stacked above `.split-view-container`.
- `.split-view-container`: row flex holding `.chat-pane` and, conditionally, the artifact pane (`ArtifactViewer.js`, class `.artifact-pane`).

**The split is binary, not resizable.** There's no drag-to-resize handle — on desktop the chat pane is either full-width or shares the row with the artifact pane, driven by `.chat-pane.shrunk`.

Responsive behavior is breakpoint-driven rather than a third layout mode:

- **Desktop (>1100px):** the sidebar remains in-flow; when an artifact opens, chat and artifact share the workspace.
- **Tablet (821–1100px):** the sidebar remains compact and the dual-pane workspace stays usable with reduced horizontal spacing.
- **Mobile (≤820px):** the sidebar becomes a fixed overlay and the artifact pane replaces the chat pane instead of forcing a 50/50 split.
- **Small mobile (≤560px):** navigation, message spacing, controls, and artifact actions are tightened for narrow screens.

## 2. State Transitions

All state lives in `page.js` (no global store) and cascades down as props — there's no separate design-state layer:

| Trigger | State change | Visual effect |
|---|---|---|
| App loads | `fetchHealth`/`fetchModels`/`fetchSessions` fire in parallel (`Promise.allSettled`); most recent session auto-loads | Sidebar populates; navbar shows health badge + default provider |
| Assistant reply contains `<<<ARTIFACT ...>>>` | `activeArtifact` is set mid-stream, as soon as the opening+closing delimiters are seen in the accumulating buffer (regex match against `accumulatedText`, not the full display text) | Artifact pane mounts; on mobile it becomes the full workspace surface, while desktop/tablet keeps the split |
| User clicks "×" on the artifact pane | `activeArtifact = null` | Artifact pane unmounts, chat pane returns to full width |
| Stream completes | `loadSession()` re-fetches the persisted session (messages + citations + artifacts) from the backend, replacing the optimistic/streamed state with the DB's version | Any Ship 30 word-count notice appended server-side becomes visible here — it wasn't part of the live stream |
| Backend served the response from a different provider than selected (fallback fired) | `page.js`'s `onComplete` handler calls `setSelectedProvider(completion.provider)` | Navbar dropdown and status badge switch to the actual serving provider automatically |
| Citation badge clicked | `activeCitation` is set | `CitationModal` opens as an overlay (not part of the split — it's a modal, independent of the two-pane layout) |
| Sidebar toggle (hamburger) | `isSidebarOpen` flips | Desktop keeps the sidebar in-flow; mobile uses the same state to slide the sidebar overlay in/out |

## 3. Artifact Pane Internals (`ArtifactViewer.js`)

- Two tabs: **Preview** (rendered) and **Code** (raw). Tab state is local to the component (`useState`), reset on remount (i.e., switching artifacts always reopens on "Preview").
- HTML artifacts render inside `<iframe sandbox="allow-scripts" srcDoc={artifact.content}>` — `allow-same-origin` is deliberately omitted (see `docs/architecture.md` §Security). Non-HTML artifacts (markdown/text) render as plain preformatted text, never through the iframe.
- Copy-to-clipboard and download-as-file actions operate on the raw `artifact.content` string directly.

## 4. Responsive Behavior

The UI now has explicit responsive breakpoints in `frontend/app/globals.css`:

- **`max-width: 1100px`:** reduces sidebar width and horizontal chat spacing while preserving the desktop information hierarchy.
- **`max-width: 820px`:** converts the sidebar to an overlay, hides the health badge to preserve navbar space, and changes the artifact pane to an absolute full-workspace layer so chat and artifacts remain readable on narrow screens.
- **`max-width: 560px`:** tightens navbar controls, message density, citation chips, input padding, and artifact actions for small phones.

The responsive strategy intentionally keeps the desktop interaction model intact while preventing the chat and artifact panes from becoming unusably narrow on tablet and mobile widths.

## 5. Accessibility Considerations

- Interactive controls remain keyboard-focusable native buttons/selects.
- Focus styles are preserved for the model selector and chat input.
- Narrow layouts avoid horizontal pane compression that would otherwise reduce readable text and control hit targets.
- The artifact viewer continues to use an isolated sandboxed iframe; responsive behavior does not change its security boundary.
