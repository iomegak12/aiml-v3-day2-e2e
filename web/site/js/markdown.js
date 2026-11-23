// README -> HTML with a safe link policy. The Marked class is injected (vendor/marked.esm.js).

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ESCAPES[c]);
}

/** "anchor" (#x), "external" (http/https/mailto), "relative" (repo file) or "unsafe". */
export function classifyLink(href) {
  const h = String(href ?? "").trim();
  if (h === "") return "unsafe";
  if (h.startsWith("#")) return "anchor";
  if (/^(https?:|mailto:)/i.test(h)) return "external";
  if (/^[a-z][a-z0-9+.-]*:/i.test(h) || h.startsWith("//")) return "unsafe";   // javascript:, data:, //host
  return "relative";
}

/** GitHub-style heading slug: "Run Locally" -> "run-locally". */
export function slugify(text) {
  return String(text)
    .toLowerCase()
    .trim()
    .replace(/<[^>]*>/g, "")
    .replace(/[^\p{L}\p{N}\s_-]/gu, "")
    .replace(/\s/g, "-");
}

/**
 * Build a Marked instance for the README:
 * - raw HTML is escaped, never rendered
 * - #anchors kept; external links open in a new tab (noopener noreferrer)
 * - relative repo links (docs/…, SECURITY.md) become plain text + <code>path</code>
 * - headings get unique slug ids; relative images become their alt text
 */
export function createReadmeRenderer(MarkedClass) {
  const used = new Map();
  const uniqueSlug = (text) => {
    const base = slugify(text) || "section";
    const count = used.get(base) ?? 0;
    used.set(base, count + 1);
    return count === 0 ? base : `${base}-${count}`;
  };

  return new MarkedClass({
    gfm: true,
    renderer: {
      html({ text }) {
        return escapeHtml(text);
      },
      heading({ tokens, depth, text }) {
        const inner = this.parser.parseInline(tokens);
        return `<h${depth} id="${uniqueSlug(text)}">${inner}</h${depth}>\n`;
      },
      link({ href, title, tokens }) {
        const inner = this.parser.parseInline(tokens);
        const kind = classifyLink(href);
        const titleAttr = title ? ` title="${escapeHtml(title)}"` : "";
        if (kind === "anchor") return `<a href="${escapeHtml(href)}"${titleAttr}>${inner}</a>`;
        if (kind === "external") {
          return `<a href="${escapeHtml(href)}"${titleAttr} target="_blank" rel="noopener noreferrer">${inner}</a>`;
        }
        if (kind === "relative") {
          const plain = inner.replace(/<[^>]*>/g, "");
          const path = escapeHtml(href);
          return plain === path || plain === href
            ? `<code class="repo-path" title="File in the repository">${path}</code>`
            : `<span class="repo-link" title="File in the repository: ${path}">${inner}</span>`;
        }
        return inner;   // unsafe scheme: text only
      },
      image({ href, text }) {
        if (classifyLink(href) !== "external") return escapeHtml(text);
        return `<img src="${escapeHtml(href)}" alt="${escapeHtml(text)}" loading="lazy">`;
      },
    },
  });
}

/** Render README markdown to HTML. */
export function renderReadme(markdown, MarkedClass) {
  return createReadmeRenderer(MarkedClass).parse(String(markdown));
}
