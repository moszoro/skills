// Source of draw.mjs. Edit this file, then rebuild the bundle: `npm install && npm run build`.
//
// Usage: node draw.mjs [--max-width N] [--html FILE]  < diagram.mmd
//   default   print the diagram as Unicode box drawing (for the chat)
//   --html    write a browser page that draws it with mermaid.js; print the page path
// Exit 2: the text renderer cannot draw this diagram type. Use --html.
import { renderMermaidASCII } from "beautiful-mermaid";
import { readFileSync, writeFileSync } from "node:fs";

const MESSAGE_WITH_LABEL = /^(\s*[^%\s].*?(?:-->>|->>|-->|->|--x|-x|--\)|-\))[^:]*:)\s*(.*)$/;

function numberSequenceSteps(source) {
  if (!/^\s*sequenceDiagram\b/.test(source) || !/^\s*autonumber\b/m.test(source)) return source;
  let step = 0;
  return source
    .split("\n")
    .filter((line) => !/^\s*autonumber\b/.test(line))
    .map((line) => line.replace(MESSAGE_WITH_LABEL, (_, head, label) => `${head} ${++step}. ${label}`))
    .join("\n");
}

function browserPage(source) {
  const payload = JSON.stringify(source).replace(/<\//g, "<\\/");
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>show-me diagram</title>
<style>
:root{--bg:#f6f4ef;--card:#fdfcfa;--ink:#2b2a27;--muted:#6c675e;--line:#e6e1d7;--bad:#ab392c}
@media (prefers-color-scheme: dark){:root{--bg:#1c1b19;--card:#262522;--ink:#ece9e2;--muted:#a39e94;--line:#3a3833;--bad:#e8806f}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1200px;margin:0 auto;padding:24px 16px 48px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;overflow-x:auto}
.card svg{max-width:100%;height:auto}
details{margin-top:12px;color:var(--muted)}
pre{white-space:pre-wrap;font:12px/1.45 ui-monospace,Menlo,monospace}
.error{color:var(--bad)}
</style>
</head>
<body>
<main><section class="card"><div id="drawing"></div><details><summary>Source</summary><pre id="source"></pre></details></section></main>
<script type="application/json" id="diagram">${payload}</script>
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
const code = JSON.parse(document.getElementById("diagram").textContent);
document.getElementById("source").textContent = code;
const drawing = document.getElementById("drawing");
mermaid.initialize({ startOnLoad: false, theme: matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "default" });
try {
  drawing.innerHTML = (await mermaid.render("diagram-svg", code)).svg;
} catch (err) {
  drawing.className = "error";
  drawing.textContent = "Could not draw: " + (err.message ?? err);
}
</script>
</body>
</html>
`;
}

function option(name) {
  const at = process.argv.indexOf(name);
  return at === -1 ? undefined : process.argv[at + 1];
}

const source = readFileSync(0, "utf8").trim();
const htmlPath = option("--html");

if (htmlPath) {
  writeFileSync(htmlPath, browserPage(source));
  console.log(htmlPath);
  process.exit(0);
}

let drawn;
try {
  drawn = renderMermaidASCII(numberSequenceSteps(source));
} catch (err) {
  console.error(`Cannot draw this diagram as text (${err.message}). Draw it in the browser: --html <file>.`);
  process.exit(2);
}

const maxWidth = Number(option("--max-width") ?? process.env.COLUMNS ?? 0);
const width = Math.max(...drawn.split("\n").map((line) => line.trimEnd().length));
if (maxWidth && width > maxWidth) {
  console.error(`Drawing is ${width} columns, wider than ${maxWidth} columns. Shorten labels or split the diagram.`);
}
process.stdout.write(drawn.split("\n").map((line) => line.trimEnd()).join("\n") + "\n");
