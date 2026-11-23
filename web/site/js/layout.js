// Shared header behaviour (DOM glue): the light / dark toggle.

import { applyTheme, loadTheme, saveTheme, toggleTheme } from "./theme.js";

function storage() {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function render(button, theme) {
  const dark = theme === "netcore-dark";
  button.setAttribute("aria-pressed", String(dark));
  button.querySelector("[data-theme-label]").textContent = dark ? "Dark" : "Light";
  button.title = dark ? "Switch to light theme" : "Switch to dark theme";
}

export function initLayout() {
  const store = storage();
  let theme = applyTheme(document, loadTheme(store));
  const button = document.getElementById("theme-toggle");
  if (!button) return;
  render(button, theme);
  button.addEventListener("click", () => {
    theme = applyTheme(document, toggleTheme(theme));
    saveTheme(store, theme);
    render(button, theme);
  });
}
