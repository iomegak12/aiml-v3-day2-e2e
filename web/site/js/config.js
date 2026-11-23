// Shared constants for the NetCore TAC ETA web UI.
// FIELD_LIMITS and ENUMS mirror TicketIn in src/netcore_tac/api/schemas.py — keep them in sync.

export const API_PREDICT_PATH = "/api/v1/predictions";

/** The business baseline the model replaces: fixed ETA per severity, in hours. */
export const FIXED_ETA_HOURS = Object.freeze({ S1: 4, S2: 24, S3: 48, S4: 72 });

export const ENUMS = Object.freeze({
  severity: Object.freeze(["S1", "S2", "S3", "S4"]),
  customer_tier: Object.freeze(["Platinum", "Gold", "Silver"]),
  region: Object.freeze(["AMER", "EMEA", "APJC"]),
  channel: Object.freeze(["Email", "Phone", "Portal"]),
});

export const FIELD_LIMITS = Object.freeze({
  product_family: Object.freeze({ minLength: 1, maxLength: 50 }),
  devices_affected: Object.freeze({ min: 1, max: 1000, integer: true }),
  software_version_months: Object.freeze({ min: 0, max: 240, integer: true }),
  prior_tickets_90d: Object.freeze({ min: 0, max: 100, integer: true }),
  engineer_experience_years: Object.freeze({ min: 0, max: 50, optional: true }),
  first_response_minutes: Object.freeze({ min: 0, max: 10080, optional: true }),
});

export const KNOWN_PRODUCTS = Object.freeze(["Firewalls", "Routers", "SD-WAN", "Switches", "Wireless"]);

/** Human labels for form fields (used in error messages and the error summary). */
export const FIELD_LABELS = Object.freeze({
  created_at: "Created at",
  product_family: "Product family",
  severity: "Severity",
  customer_tier: "Customer tier",
  region: "Region",
  channel: "Channel",
  devices_affected: "Devices affected",
  software_version_months: "Software age (months)",
  prior_tickets_90d: "Prior tickets (90 days)",
  engineer_experience_years: "Engineer experience (years)",
  first_response_minutes: "First response (minutes)",
});

export const THEMES = Object.freeze([
  Object.freeze({ id: "netcore-light", label: "Light" }),
  Object.freeze({ id: "netcore-dark", label: "Dark" }),
]);
export const DEFAULT_THEME = "netcore-light";
export const THEME_STORAGE_KEY = "netcore-tac-theme";

export const HISTORY_STORAGE_KEY = "netcore-tac-history";
export const HISTORY_MAX = 20;

export const REQUEST_TIMEOUT_MS = 10000;
