---
name: show-me
description: "Help the user understand the current topic visually with concise diagrams, code-shape sketches, and focused HTML artifacts — and DRAW every Mermaid diagram in the chat instead of leaving it as text. Use when the user runs /show-me, asks to see or visualise something, or whenever you are about to show a Mermaid diagram in a terminal chat."
allowed-tools: Bash(node ${CLAUDE_SKILL_DIR}/scripts/draw.mjs *)
---

Help the user understand the current topic of conversation visually. Skip the preamble and keep prose brief. Pick the smallest view that makes the key point clear.

## Mermaid is never left as text

The terminal cannot draw Mermaid. A ```` ```mermaid ```` block reaches the user as raw source. So for every Mermaid diagram:

1. Draw it with the bundled renderer. Pass the Mermaid on stdin:

   ```bash
   node "${CLAUDE_SKILL_DIR}/scripts/draw.mjs" --max-width 160 <<'MMD'
   sequenceDiagram
       participant User
       participant UI
       User->>UI: choose command
   MMD
   ```

2. Copy the output **verbatim** into your reply, inside a ```` ```text ```` block. The user does not reliably see tool output, so the drawing must be in your own message. Do not also paste the Mermaid source unless the user asks for it.
3. If stderr says the drawing is too wide, shorten the labels or split the diagram, and draw it again.
4. Exit code 2 means the text renderer cannot draw this type (pie, gantt, mindmap, timeline, ...). Then write a browser page and open it:

   ```bash
   node "${CLAUDE_SKILL_DIR}/scripts/draw.mjs" --html /tmp/show-me-<topic>.html <<'MMD'
   ...
   MMD
   open /tmp/show-me-<topic>.html
   ```

   Use your scratchpad directory instead of `/tmp` when you have one. Tell the user the page opened.

The text renderer draws flowcharts, sequence diagrams (with `alt`/`loop` boxes, notes and `autonumber`), state, class and ER diagrams, and xy charts.

## Pick the view

- Show logic or an algorithm as pseudocode:

```text
on(save)
  if content is unchanged
    return cached result
  write new content
  return fresh result
```

- Show runtime control flow as a call tree:

```text
submitForm
  createSession
    persistPrompt
    launchAgent
  navigateToSession
```

- Show UI structure as a component tree, including state and module boundaries that matter:

```tsx
<SessionPage> (apps/example/src/routes/session.tsx)
  useSessionEvents()
  <SessionToolbar>
    <RunSkillButton> (packages/ui)
```

- Show file responsibility or a broad refactor as a shallow file tree:

```text
src/
├── commands/       # parses user actions
├── sessions/       # owns session state
└── transport/      # sends API requests
```

- Show component interaction, control flow, or data flow with Mermaid, drawn as described above.

- Use `diff` when the point is what changes and the surrounding shape already exists. Match the diff shape to the topic:

```diff
 <SessionPage>
   useSessionEvents()
   <SessionToolbar>
+    <RunSkillButton />
   <SessionTimeline>
+    <SkillResultCard />
```

```diff
 submitForm
   createSession
     persistPrompt
+    expandSkillMention
     launchAgent
```

- Show the whole block when most of it is new, when omitted context would hide ownership or order, or when the user needs a copyable target shape.

- For a visual UI, layout, state comparison, or concept too dense for a diagram, write one focused HTML file — a diagram, an infographic, or a short slide deck, whichever fits the point. Match the product's colors, type, spacing, and components; use real labels and data; support desktop and mobile. Then `open` it for the user.

## Guidance

Place each visual next to the short text it supports. Keep only the calls, files, props, states, and boundaries needed to answer the user's current question or the options to resolve the current discussion point.

You may use one of these, you may use several, it is unlikely you will use all of them. Use your judgement and don't overwhelm the user.

---

Based on `show-me` from [humanlayer/skills](https://github.com/humanlayer/skills) (MIT). Text drawing by [beautiful-mermaid](https://github.com/lukilabs/beautiful-mermaid) (MIT), bundled in `scripts/draw.mjs`; rebuild it from `scripts/draw.src.mjs` with `npm install && npm run build`.
