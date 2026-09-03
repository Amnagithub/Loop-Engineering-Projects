#!/usr/bin/env node
// render-transcript.js — turn a routine run's transcript.jsonl into readable
// text showing every assistant message, tool call, and tool result.
// Usage: node render-transcript.js <transcript.jsonl> [<output.txt>]
const fs = require("fs");
const file = process.argv[2];
const out = process.argv[3];
if (!file) { console.error("usage: node render-transcript.js <transcript.jsonl> [out.txt]"); process.exit(1); }

const lines = fs.readFileSync(file, "utf8").split("\n").filter(Boolean);
const parts = [];

const clip = (s, n = 240) => {
  s = String(s);
  return s.length > n ? s.slice(0, n) + "…" : s;
};

const inputSummary = (input) => {
  if (!input) return "";
  const keys = Object.keys(input);
  const picked = {};
  for (const k of keys) {
    const v = input[k];
    if (v === undefined || v === null) continue;
    picked[k] = typeof v === "string" ? v : JSON.stringify(v);
  }
  const text = JSON.stringify(picked);
  return text.length > 300 ? text.slice(0, 300) + "…" : text;
};

for (const line of lines) {
  let e; try { e = JSON.parse(line); } catch { continue; }
  if (e.type === "assistant" && e.message && e.message.content) {
    for (const c of e.message.content) {
      if (c.type === "text" && c.text) parts.push("CLAUDE: " + c.text);
      else if (c.type === "tool_use") parts.push(`TOOL ${c.name}(${clip(inputSummary(c.input), 300)})`);
      else if (c.type === "thinking" && c.thinking) parts.push("  [thinking…]");
    }
  } else if (e.type === "user" && e.message && e.message.content) {
    const arr = Array.isArray(e.message.content) ? e.message.content : [e.message.content];
    for (const c of arr) {
      if (c.type === "tool_result") {
        let r = "";
        if (typeof c.content === "string") r = c.content;
        else if (Array.isArray(c.content)) r = c.content.map(x => x.text ?? JSON.stringify(x)).join(" ");
        const err = c.is_error ? " [ERROR]" : "";
        parts.push(`  ↳ tool_result${err}: ${clip(r, 400)}`);
      } else if (c.type === "text" && c.text && !c.text.startsWith("<")) {
        parts.push("USER: " + clip(c.text, 400));
      }
    }
  }
}

const text = parts.join("\n\n");
if (out) fs.writeFileSync(out, text);
else process.stdout.write(text);
