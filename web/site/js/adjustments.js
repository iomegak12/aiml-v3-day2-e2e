// Human-readable lines for PredictionOut.adjusted_inputs (inputs clamped to the training range).

import { FIELD_LABELS } from "./config.js";

function formatValue(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value);
  return Number.isInteger(n) ? String(n) : String(Math.round(n * 10) / 10);
}

/**
 * [{field: "engineer_experience_years", original: 35, used: 20}]
 *   -> ["Engineer experience (years): 35 → 20"]
 * Malformed entries are skipped; unknown fields keep their API name.
 * @param {unknown} list
 * @returns {string[]}
 */
export function formatAdjustments(list) {
  if (!Array.isArray(list)) return [];
  return list
    .filter((a) => a && typeof a.field === "string" && a.original !== undefined && a.used !== undefined)
    .map((a) => `${FIELD_LABELS[a.field] ?? a.field}: ${formatValue(a.original)} → ${formatValue(a.used)}`);
}
