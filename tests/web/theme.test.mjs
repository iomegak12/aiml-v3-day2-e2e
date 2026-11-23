// Unit tests for web/site/js/theme.js
import { test } from "node:test";
import assert from "node:assert/strict";

import { applyTheme, loadTheme, resolveTheme, saveTheme, toggleTheme } from "../../web/site/js/theme.js";

function memoryStorage() {
  const data = new Map();
  return { getItem: (k) => (data.has(k) ? data.get(k) : null), setItem: (k, v) => data.set(k, String(v)) };
}
const throwing = { getItem() { throw new Error("x"); }, setItem() { throw new Error("x"); } };

test("resolveTheme accepts known ids only", () => {
  assert.equal(resolveTheme("netcore-dark"), "netcore-dark");
  assert.equal(resolveTheme("netcore-light"), "netcore-light");
  assert.equal(resolveTheme("plum-coral"), "netcore-light");
  assert.equal(resolveTheme(null), "netcore-light");
});

test("save and load round trip", () => {
  const storage = memoryStorage();
  assert.equal(loadTheme(storage), "netcore-light");
  assert.equal(saveTheme(storage, "netcore-dark"), true);
  assert.equal(loadTheme(storage), "netcore-dark");
});

test("unknown saved value falls back to light", () => {
  const storage = memoryStorage();
  storage.setItem("netcore-tac-theme", "neon");
  assert.equal(loadTheme(storage), "netcore-light");
});

test("blocked storage never throws", () => {
  assert.equal(loadTheme(throwing), "netcore-light");
  assert.equal(saveTheme(throwing, "netcore-dark"), false);
  assert.equal(saveTheme(null, "netcore-dark"), false);
});

test("applyTheme sets data-theme on <html>", () => {
  const attrs = {};
  const doc = { documentElement: { setAttribute: (k, v) => { attrs[k] = v; } } };
  assert.equal(applyTheme(doc, "netcore-dark"), "netcore-dark");
  assert.equal(attrs["data-theme"], "netcore-dark");
  assert.equal(applyTheme(doc, "bogus"), "netcore-light");
});

test("toggleTheme switches light and dark", () => {
  assert.equal(toggleTheme("netcore-light"), "netcore-dark");
  assert.equal(toggleTheme("netcore-dark"), "netcore-light");
  assert.equal(toggleTheme("bogus"), "netcore-dark");
});
