// Run: node --test skills/show-me/scripts/
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const DRAW = new URL("./draw.mjs", import.meta.url).pathname;
const draw = (mermaid, ...args) => spawnSync("node", [DRAW, ...args], { input: mermaid, encoding: "utf8" });

const ANNA = `sequenceDiagram
    autonumber
    participant Anna as Anna (mini-app)
    participant API as Aura API
    Anna->>API: show my results
    alt refused
        API-->>Anna: not found
    else allowed
        API-->>Anna: her results
    end`;

test("draws a sequence diagram as box-drawing text", () => {
  const run = draw(ANNA);
  assert.equal(run.status, 0, run.stderr);
  assert.match(run.stdout, /│ Anna \(mini-app\) │/);
  assert.match(run.stdout, /alt \[refused\]/);
  assert.match(run.stdout, /[─╌]+▶/);
});

test("keeps autonumber as step numbers in the message labels", () => {
  const out = draw(ANNA).stdout;
  assert.match(out, /1\. show my results/);
  assert.match(out, /2\. not found/);
  assert.match(out, /3\. her results/);
});

test("draws a flowchart", () => {
  const run = draw("flowchart LR\n  A[Upload] --> B{Readable?}\n  B -->|yes| C[Store]");
  assert.equal(run.status, 0, run.stderr);
  for (const label of ["Upload", "Readable?", "Store", "yes"]) assert.ok(run.stdout.includes(label), label);
});

test("a type the text renderer cannot draw exits 2 and says to use --html", () => {
  const run = draw('pie title Pets\n  "Dogs" : 386\n  "Cats" : 85');
  assert.equal(run.status, 2);
  assert.equal(run.stdout, "");
  assert.match(run.stderr, /--html/);
});

test("warns on stderr when the drawing is wider than --max-width", () => {
  const run = draw(ANNA, "--max-width", "20");
  assert.equal(run.status, 0);
  assert.match(run.stderr, /wider than 20 columns/);
});

test("--html writes a browser page that carries the source safely", () => {
  const page = join(mkdtempSync(join(tmpdir(), "show-me-")), "d.html");
  const hostile = "pie title x</script><script>alert(1)\n  \"a\" : 1";
  const run = draw(hostile, "--html", page);
  assert.equal(run.status, 0, run.stderr);
  const html = readFileSync(page, "utf8");
  assert.ok(html.includes("mermaid@11"));
  assert.ok(!html.includes("</script><script>alert(1)"));
  const payload = html.split('<script type="application/json" id="diagram">')[1].split("</script>")[0];
  assert.equal(JSON.parse(payload), hostile);
  assert.equal(run.stdout.trim(), page);
});
