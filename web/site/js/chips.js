// Sample tickets ("chips") that fill the Register Ticket form in one click.

const pad = (n) => String(n).padStart(2, "0");

/** Local date-time in the datetime-local format: "YYYY-MM-DDTHH:mm". */
export function formatLocalDateTime(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
    + `T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function atTime(date, hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  const d = new Date(date.getTime());
  d.setHours(h, m, 0, 0);
  return d;
}

/**
 * Resolve a chip's "when" rule against ``now``.
 * - {type: "now"}                         -> now (minutes precision)
 * - {type: "today", time: "02:10"}        -> today at that time
 * - {type: "last-saturday", time: "10:30"}-> the latest Saturday at that time that is not after now
 */
export function resolveCreatedAt(when, now) {
  if (when.type === "today") return formatLocalDateTime(atTime(now, when.time));
  if (when.type === "last-saturday") {
    let candidate = atTime(now, when.time);
    candidate.setDate(candidate.getDate() - ((candidate.getDay() + 1) % 7));   // back to Saturday
    if (candidate > now) candidate.setDate(candidate.getDate() - 7);
    return formatLocalDateTime(candidate);
  }
  return formatLocalDateTime(now);
}

export const SAMPLE_TICKETS = Object.freeze([
  {
    id: "s1-router",
    label: "S1 · Core router outage",
    when: { type: "today", time: "02:10" },
    values: { product_family: "Routers", severity: "S1", customer_tier: "Platinum", region: "AMER",
              channel: "Phone", devices_affected: 25, software_version_months: 18, prior_tickets_90d: 3,
              engineer_experience_years: 9.5, first_response_minutes: 5 },
  },
  {
    id: "s2-firewall",
    label: "S2 · Weekend firewall",
    when: { type: "last-saturday", time: "10:30" },
    values: { product_family: "Firewalls", severity: "S2", customer_tier: "Gold", region: "EMEA",
              channel: "Phone", devices_affected: 4, software_version_months: 40, prior_tickets_90d: 1,
              engineer_experience_years: 6.5, first_response_minutes: 20 },
  },
  {
    id: "s3-switch",
    label: "S3 · Old switch software",
    when: { type: "now" },
    values: { product_family: "Switches", severity: "S3", customer_tier: "Silver", region: "APJC",
              channel: "Portal", devices_affected: 12, software_version_months: 60, prior_tickets_90d: 5,
              engineer_experience_years: 3, first_response_minutes: 95 },
  },
  {
    id: "s4-wireless",
    label: "S4 · Wireless question",
    when: { type: "now" },
    values: { product_family: "Wireless", severity: "S4", customer_tier: "Silver", region: "EMEA",
              channel: "Email", devices_affected: 1, software_version_months: 6, prior_tickets_90d: 0,
              engineer_experience_years: 12, first_response_minutes: 240 },
  },
  {
    id: "unknown-product",
    label: "Unknown product, missing data",
    when: { type: "now" },
    values: { product_family: "Optical Transport", severity: "S2", customer_tier: "Gold", region: "AMER",
              channel: "Portal", devices_affected: 8, software_version_months: 30, prior_tickets_90d: 2,
              engineer_experience_years: null, first_response_minutes: null },
  },
]);

/** Form values (all strings; null -> "") for a chip, with created_at resolved against ``now``. */
export function chipToFormValues(chip, now) {
  const values = { created_at: resolveCreatedAt(chip.when, now) };
  for (const [field, value] of Object.entries(chip.values)) {
    values[field] = value === null ? "" : String(value);
  }
  return values;
}
