// Form values (strings) -> TicketIn payload, plus client-side checks that mirror the API.

import { ENUMS, FIELD_LABELS, FIELD_LIMITS } from "./config.js";

const DATETIME_LOCAL = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;
const DATETIME_ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/;

function text(value) {
  return value === undefined || value === null ? "" : String(value).trim();
}

/** "2026-11-23T10:15" (datetime-local) -> "2026-11-23T10:15:00"; other strings unchanged. */
export function toIsoDateTime(value) {
  const s = text(value);
  return DATETIME_LOCAL.test(s) ? `${s}:00` : s;
}

/** Required number: blank -> NaN (so validation reports it). */
export function toNumber(value) {
  const s = text(value);
  return s === "" ? Number.NaN : Number(s);
}

/** Optional number: blank -> null (the API fills it with the training median). */
export function toOptionalNumber(value) {
  const s = text(value);
  return s === "" ? null : Number(s);
}

/**
 * Build the JSON body for POST /api/v1/predictions.
 * @param {Record<string, string|number|null|undefined>} values raw form values keyed by field name
 */
export function formToPayload(values) {
  return {
    created_at: toIsoDateTime(values.created_at),
    product_family: text(values.product_family),
    severity: text(values.severity),
    customer_tier: text(values.customer_tier),
    region: text(values.region),
    channel: text(values.channel),
    devices_affected: toNumber(values.devices_affected),
    software_version_months: toNumber(values.software_version_months),
    prior_tickets_90d: toNumber(values.prior_tickets_90d),
    engineer_experience_years: toOptionalNumber(values.engineer_experience_years),
    first_response_minutes: toOptionalNumber(values.first_response_minutes),
  };
}

function isValidDateTime(value) {
  if (!DATETIME_ISO.test(value)) return false;
  const [date, time] = value.split("T");
  const [y, m, d] = date.split("-").map(Number);
  const [hh, mm, ss] = time.split(":").map(Number);
  const dt = new Date(y, m - 1, d, hh, mm, ss);
  return dt.getFullYear() === y && dt.getMonth() === m - 1 && dt.getDate() === d
    && hh < 24 && mm < 60 && ss < 60;
}

function checkNumber(value, limits) {
  if (value === null && limits.optional) return null;
  const range = `${limits.min} to ${limits.max}`;
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return limits.optional ? `Enter a number from ${range}, or leave blank` : `Enter a number from ${range}`;
  }
  if (limits.integer && !Number.isInteger(value)) return `Enter a whole number from ${range}`;
  if (value < limits.min || value > limits.max) {
    return limits.integer ? `Enter a whole number from ${range}` : `Enter a number from ${range}`;
  }
  return null;
}

/**
 * Same rules as TicketIn. Returns {} when valid, else {field: message}.
 * @param {ReturnType<typeof formToPayload>} payload
 */
export function validatePayload(payload) {
  const errors = {};
  if (!isValidDateTime(payload.created_at)) errors.created_at = "Enter a valid date and time";

  const { minLength, maxLength } = FIELD_LIMITS.product_family;
  const len = payload.product_family.length;
  if (len < minLength || len > maxLength) {
    errors.product_family = `Enter ${minLength} to ${maxLength} characters`;
  }

  for (const [field, allowed] of Object.entries(ENUMS)) {
    if (!allowed.includes(payload[field])) {
      errors[field] = `Choose a ${FIELD_LABELS[field].toLowerCase()}`;
    }
  }

  for (const [field, limits] of Object.entries(FIELD_LIMITS)) {
    if (field === "product_family") continue;
    const message = checkNumber(payload[field], limits);
    if (message) errors[field] = message;
  }
  return errors;
}
