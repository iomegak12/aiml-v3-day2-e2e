// Unit tests for web/site/js/markdown.js (with the vendored marked build)
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import { Marked } from "../../web/site/vendor/marked.esm.js";
import { classifyLink, escapeHtml, renderReadme, slugify } from "../../web/site/js/markdown.js";

test("classifyLink", () => {
  assert.equal(classifyLink("#setup"), "anchor");
  assert.equal(classifyLink("https://example.com"), "external");
  assert.equal(classifyLink("mailto:a@example.com"), "external");
  assert.equal(classifyLink("docs/02-model-rest-api.md"), "relative");
  assert.equal(classifyLink("SECURITY.md"), "relative");
  assert.equal(classifyLink("javascript:alert(1)"), "unsafe");
  assert.equal(classifyLink("data:text/html,x"), "unsafe");
  assert.equal(classifyLink("//evil.example"), "unsafe");
  assert.equal(classifyLink(""), "unsafe");
});

test("slugify like GitHub", () => {
  assert.equal(slugify("Run Locally"), "run-locally");
  assert.equal(slugify("Docker / Compose"), "docker--compose");
  assert.equal(slugify("Day 2 — TAC Desk"), "day-2--tac-desk");
});

test("escapeHtml", () => {
  assert.equal(escapeHtml(`<a href="x">'&'</a>`), "&lt;a href=&quot;x&quot;&gt;&#39;&amp;&#39;&lt;/a&gt;");
});

test("raw HTML is escaped, never rendered", () => {
  const html = renderReadme("<script>alert(1)</script>\n\nText <b>bold</b>", Marked);
  assert.ok(!html.includes("<script>"));
  assert.ok(!html.includes("<b>"));
  assert.ok(html.includes("&lt;script&gt;"));
});

test("link policy", () => {
  const html = renderReadme("[top](#setup) [ext](https://example.com) [SECURITY.md](SECURITY.md) "
    + "[the log](docs/02.md) [bad](javascript:alert(1))", Marked);
  assert.ok(html.includes('<a href="#setup">top</a>'));
  assert.ok(html.includes('href="https://example.com" target="_blank" rel="noopener noreferrer"'));
  assert.ok(html.includes('<code class="repo-path" title="File in the repository">SECURITY.md</code>'));
  assert.ok(html.includes('<span class="repo-link" title="File in the repository: docs/02.md">the log</span>'));
  assert.ok(!html.includes("javascript:"));
});

test("headings get unique slug ids", () => {
  const html = renderReadme("## Setup\n\n## Setup\n", Marked);
  assert.ok(html.includes('<h2 id="setup">Setup</h2>'));
  assert.ok(html.includes('<h2 id="setup-1">Setup</h2>'));
});

test("relative images become alt text", () => {
  assert.ok(!renderReadme("![diagram](docs/arch.png)", Marked).includes("<img"));
});

test("the project README renders with tables and code", () => {
  const readme = readFileSync(new URL("../../README.md", import.meta.url), "utf8");
  const html = renderReadme(readme, Marked);
  assert.ok(html.includes("<table>"));
  assert.ok(html.includes("<pre><code"));
  assert.ok(!/href="(?!#|https?:|mailto:)/.test(html), "no relative hrefs left");
});
