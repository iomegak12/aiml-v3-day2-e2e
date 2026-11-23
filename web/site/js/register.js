// Register Ticket page controller (DOM glue). All rules live in the pure modules it imports.

import { predict } from "./api.js";
import { chipToFormValues, formatLocalDateTime, SAMPLE_TICKETS } from "./chips.js";
import { FIELD_LABELS } from "./config.js";
import { compareWithFixed, formatDuration, formatHours } from "./eta.js";
import { createHistory } from "./history.js";
import { initLayout } from "./layout.js";
import { formToPayload, validatePayload } from "./payload.js";

const FIELDS = Object.keys(FIELD_LABELS);
const $ = (id) => document.getElementById(id);

const form = $("ticket-form");
const submit = $("submit-btn");
const chipList = $("chips");
const summary = $("error-summary");
const banner = $("status-banner");
const resultEmpty = $("result-empty");
const resultBody = $("result-body");
const resultHeading = $("result-heading");

function sessionStore() {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}
const history = createHistory(sessionStore());
let countdownTimer = null;

// ---------- helpers ----------
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function input(field) {
  return form.elements.namedItem(field);
}

function readForm() {
  return Object.fromEntries(FIELDS.map((f) => [f, input(f).value]));
}

function fillForm(values) {
  for (const [field, value] of Object.entries(values)) input(field).value = value;
}

function setChipPressed(id) {
  for (const chip of chipList.querySelectorAll(".chip")) {
    chip.setAttribute("aria-pressed", String(chip.dataset.chip === id));
  }
}

// ---------- errors ----------
function clearErrors() {
  summary.hidden = true;
  summary.replaceChildren();
  for (const field of FIELDS) {
    const control = input(field);
    control.removeAttribute("aria-invalid");
    const message = $(`err-${field}`);
    message.hidden = true;
    message.textContent = "";
  }
}

function showFieldErrors(errors) {
  const entries = Object.entries(errors);
  const list = el("ul");
  for (const [field, message] of entries) {
    const known = FIELDS.includes(field);
    if (known) {
      input(field).setAttribute("aria-invalid", "true");
      const node = $(`err-${field}`);
      node.textContent = message;
      node.hidden = false;
    }
    const item = el("li");
    if (known) {
      const link = el("a", "", `${FIELD_LABELS[field]}: ${message}`);
      link.href = `#field-${field}`;
      link.addEventListener("click", (event) => {
        event.preventDefault();
        input(field).focus();
      });
      item.appendChild(link);
    } else {
      item.textContent = `${field}: ${message}`;
    }
    list.appendChild(item);
  }
  summary.replaceChildren(el("h3", "", `Please fix ${entries.length} field${entries.length === 1 ? "" : "s"}`), list);
  summary.hidden = false;
  summary.focus();
}

// ---------- banners ----------
function hideBanner() {
  banner.hidden = true;
  banner.textContent = "";
  banner.className = "banner";
}

function showBanner(kind, message) {
  banner.className = `banner ${kind === "warn" ? "banner-warn" : "banner-error"}`;
  banner.textContent = message;
  banner.hidden = false;
}

function startCountdown(seconds) {
  clearInterval(countdownTimer);
  let remaining = Math.max(1, seconds);
  const tick = () => {
    if (remaining <= 0) {
      clearInterval(countdownTimer);
      countdownTimer = null;
      hideBanner();
      submit.disabled = false;
      return;
    }
    showBanner("warn", `Too many requests. Try again in ${remaining} s.`);
    submit.disabled = true;
    remaining -= 1;
  };
  tick();
  countdownTimer = setInterval(tick, 1000);
}

function withRequestId(message, requestId) {
  return requestId ? `${message} (request ${requestId})` : message;
}

function showFailure(result) {
  switch (result.kind) {
    case "validation":
      showFieldErrors(Object.keys(result.fieldErrors).length ? result.fieldErrors
        : { body: result.problem?.detail ?? "The request was rejected" });
      break;
    case "rate-limited":
      startCountdown(result.retryAfter || 30);
      break;
    case "not-ready":
      showBanner("error", withRequestId("The prediction model isn't ready. Try again shortly.", result.requestId));
      break;
    case "unavailable":
      showBanner("error", "The prediction service is unavailable. Try again shortly.");
      break;
    case "timeout":
      showBanner("error", "The prediction service took too long to answer. Try again.");
      break;
    case "network":
      showBanner("error", "Could not reach the server. Check your connection and try again.");
      break;
    default:
      showBanner("error", withRequestId("Something went wrong on the server.", result.requestId));
  }
}

// ---------- result + history ----------
function showResult(payload, data, requestId) {
  const hours = data.predicted_hours;
  const comparison = compareWithFixed(payload.severity, hours);
  $("eta-hours").textContent = `${formatHours(hours)} h`;
  $("eta-human").textContent = `≈ ${formatDuration(hours)} to resolve`;
  $("eta-fixed").textContent = `Fixed ${payload.severity} ETA: ${comparison.fixed} h`;
  $("eta-delta").textContent = comparison.label;
  $("eta-meta").textContent = `model ${data.model_version} · request ${requestId ?? data.request_id}`;
  resultEmpty.hidden = true;
  resultBody.hidden = false;
  resultHeading.focus();

  history.add({
    created_at: payload.created_at,
    severity: payload.severity,
    product_family: payload.product_family,
    customer_tier: payload.customer_tier,
    predicted_hours: hours,
    fixed: comparison.fixed,
    delta_label: comparison.label,
  });
  renderHistory();
}

function renderHistory() {
  const rows = history.list();
  const tbody = $("history-body");
  tbody.replaceChildren();
  for (const entry of rows) {
    const tr = el("tr");
    tr.appendChild(el("td", "", entry.id));
    tr.appendChild(el("td", "", String(entry.created_at).replace("T", " ").slice(0, 16)));
    const sevCell = el("td");
    sevCell.appendChild(el("span", `badge sev-${entry.severity}`, entry.severity));
    tr.appendChild(sevCell);
    tr.appendChild(el("td", "", entry.product_family));
    tr.appendChild(el("td", "", entry.customer_tier));
    tr.appendChild(el("td", "", `${formatHours(entry.predicted_hours)} h`));
    tr.appendChild(el("td", "", `${entry.fixed} h`));
    tr.appendChild(el("td", "", entry.delta_label));
    tbody.appendChild(tr);
  }
  $("history-table").hidden = rows.length === 0;
  $("history-empty").hidden = rows.length > 0;
  $("history-clear").disabled = rows.length === 0;
}

// ---------- events ----------
function renderChips() {
  for (const chip of SAMPLE_TICKETS) {
    const li = el("li");
    const button = el("button", "chip", chip.label);
    button.type = "button";
    button.dataset.chip = chip.id;
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      fillForm(chipToFormValues(chip, new Date()));
      setChipPressed(chip.id);
      clearErrors();
    });
    li.appendChild(button);
    chipList.appendChild(li);
  }
}

async function onSubmit(event) {
  event.preventDefault();
  if (countdownTimer) return;
  clearErrors();
  if (!banner.classList.contains("banner-warn")) hideBanner();

  const payload = formToPayload(readForm());
  const errors = validatePayload(payload);
  if (Object.keys(errors).length) {
    showFieldErrors(errors);
    return;
  }

  submit.disabled = true;
  submit.textContent = "Predicting…";
  const result = await predict(payload);
  submit.textContent = "Get ETA";
  submit.disabled = false;

  if (result.ok) {
    hideBanner();
    showResult(payload, result.data, result.requestId);
  } else {
    showFailure(result);
  }
}

function setDefaultCreatedAt() {
  const now = formatLocalDateTime(new Date());
  input("created_at").defaultValue = now;
  input("created_at").value = now;
}

initLayout();
renderChips();
setDefaultCreatedAt();
renderHistory();
form.addEventListener("submit", onSubmit);
form.addEventListener("input", () => setChipPressed(null));
form.addEventListener("reset", () => {
  setChipPressed(null);
  clearErrors();
  setTimeout(setDefaultCreatedAt, 0);   // after the browser restores default values
});
$("history-clear").addEventListener("click", () => {
  history.clear();
  renderHistory();
});
