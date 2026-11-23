// Display helpers for predicted hours and the comparison with the fixed severity ETA.

import { FIXED_ETA_HOURS } from "./config.js";

const MINUS = "−";

/** 8 -> "8", 8.46 -> "8.5" (one decimal, no trailing ".0"). */
export function formatHours(value) {
  const rounded = Math.round(value * 10) / 10;
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1);
}

/** 16.3 -> "16.3 h", 32.5 -> "1 d 8.5 h", 48 -> "2 d"; negatives clamp to 0. */
export function formatDuration(hours) {
  const tenths = Math.round(Math.max(0, Number(hours) || 0) * 10);
  const days = Math.floor(tenths / 240);
  const rest = (tenths - days * 240) / 10;
  if (days === 0) return `${formatHours(rest)} h`;
  return rest === 0 ? `${days} d` : `${days} d ${formatHours(rest)} h`;
}

/**
 * Compare a prediction with the fixed ETA for its severity.
 * @returns {{fixed: number, delta: number, label: string}}
 */
export function compareWithFixed(severity, hours) {
  const fixed = FIXED_ETA_HOURS[severity];
  if (fixed === undefined) throw new RangeError(`Unknown severity: ${severity}`);
  const delta = Math.round((hours - fixed) * 10) / 10;
  let label = "Same as fixed";
  if (delta > 0) label = `+${formatHours(delta)} h vs fixed`;
  if (delta < 0) label = `${MINUS}${formatHours(-delta)} h vs fixed`;
  return { fixed, delta, label };
}
