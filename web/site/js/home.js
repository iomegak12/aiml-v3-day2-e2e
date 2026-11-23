// Home page controller (DOM glue): load README.md and render it.

import { Marked } from "../vendor/marked.esm.js";
import { initLayout } from "./layout.js";
import { renderReadme } from "./markdown.js";

const article = document.getElementById("readme");
const status = document.getElementById("readme-status");
const errorBox = document.getElementById("readme-error");
const retry = document.getElementById("readme-retry");

function wrapTables(root) {
  for (const table of root.querySelectorAll("table")) {
    const wrapper = document.createElement("div");
    wrapper.className = "table-scroll";
    table.replaceWith(wrapper);
    wrapper.appendChild(table);
  }
}

async function load() {
  status.hidden = false;
  errorBox.hidden = true;
  article.hidden = true;
  try {
    const response = await fetch("/README.md", { cache: "no-cache" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    // README comes from our own image; raw HTML is escaped and the CSP blocks inline script.
    article.innerHTML = renderReadme(await response.text(), Marked);
    wrapTables(article);
    article.hidden = false;
    if (location.hash) document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView();
  } catch {
    errorBox.hidden = false;
  } finally {
    status.hidden = true;
  }
}

initLayout();
retry.addEventListener("click", load);
load();
