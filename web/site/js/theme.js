// NetCore light / dark theme: resolve, persist (localStorage) and apply.
// theme-init.js repeats the minimal "apply saved theme" step in <head> to avoid a flash.

import { DEFAULT_THEME, THEMES, THEME_STORAGE_KEY } from "./config.js";

/** A known theme id, else the fallback. */
export function resolveTheme(value, themes = THEMES, fallback = DEFAULT_THEME) {
  return themes.some((t) => t.id === value) ? value : fallback;
}

/** Saved theme (or the default); never throws. */
export function loadTheme(storage) {
  try {
    return resolveTheme(storage?.getItem(THEME_STORAGE_KEY));
  } catch {
    return DEFAULT_THEME;
  }
}

/** Save the theme; returns false when storage is unavailable. */
export function saveTheme(storage, id) {
  try {
    if (!storage) return false;
    storage.setItem(THEME_STORAGE_KEY, resolveTheme(id));
    return true;
  } catch {
    return false;
  }
}

/** Set data-theme on <html>; returns the applied id. */
export function applyTheme(doc, id) {
  const theme = resolveTheme(id);
  doc.documentElement.setAttribute("data-theme", theme);
  return theme;
}

/** netcore-light <-> netcore-dark */
export function toggleTheme(id) {
  return resolveTheme(id) === "netcore-dark" ? "netcore-light" : "netcore-dark";
}
