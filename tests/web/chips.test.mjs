// Unit tests for web/site/js/chips.js
import { test } from "node:test";
import assert from "node:assert/strict";

import { chipToFormValues, formatLocalDateTime, resolveCreatedAt, SAMPLE_TICKETS } from "../../web/site/js/chips.js";
import { formToPayload, validatePayload } from "../../web/site/js/payload.js";

// Local-time dates: 2026-11-21 is a Saturday
const at = (y, m, d, h = 0, min = 0) => new Date(y, m - 1, d, h, min);

test("formatLocalDateTime pads to datetime-local format", () => {
  assert.equal(formatLocalDateTime(at(2026, 3, 5, 7, 4)), "2026-03-05T07:04");
});

test("now and today rules", () => {
  const now = at(2026, 11, 23, 14, 37);
  assert.equal(resolveCreatedAt({ type: "now" }, now), "2026-11-23T14:37");
  assert.equal(resolveCreatedAt({ type: "today", time: "02:10" }, now), "2026-11-23T02:10");
});

test("most recent Saturday 10:30 for every weekday", () => {
  const rule = { type: "last-saturday", time: "10:30" };
  const expected = {
    22: "2026-11-21T10:30", 23: "2026-11-21T10:30", 24: "2026-11-21T10:30", 25: "2026-11-21T10:30",
    26: "2026-11-21T10:30", 27: "2026-11-21T10:30",
  };
  for (const [day, value] of Object.entries(expected)) {
    assert.equal(resolveCreatedAt(rule, at(2026, 11, Number(day), 12)), value, `day ${day}`);
  }
});

test("Saturday before and after 10:30", () => {
  const rule = { type: "last-saturday", time: "10:30" };
  assert.equal(resolveCreatedAt(rule, at(2026, 11, 21, 9, 0)), "2026-11-14T10:30");
  assert.equal(resolveCreatedAt(rule, at(2026, 11, 21, 10, 30)), "2026-11-21T10:30");
  assert.equal(resolveCreatedAt(rule, at(2026, 11, 21, 18, 0)), "2026-11-21T10:30");
});

test("five chips, each filling every field with a valid payload", () => {
  assert.equal(SAMPLE_TICKETS.length, 5);
  const now = at(2026, 11, 23, 14, 0);
  for (const chip of SAMPLE_TICKETS) {
    const values = chipToFormValues(chip, now);
    assert.equal(Object.keys(values).length, 11, chip.id);
    assert.deepEqual(validatePayload(formToPayload(values)), {}, chip.id);
  }
});

test("unknown-product chip leaves optional fields blank", () => {
  const chip = SAMPLE_TICKETS.find((c) => c.id === "unknown-product");
  const values = chipToFormValues(chip, at(2026, 11, 23));
  assert.equal(values.engineer_experience_years, "");
  assert.equal(values.first_response_minutes, "");
  assert.equal(formToPayload(values).engineer_experience_years, null);
});

test("weekend chip lands on a Saturday", () => {
  const chip = SAMPLE_TICKETS.find((c) => c.id === "s2-firewall");
  const created = chipToFormValues(chip, at(2026, 11, 25, 8)).created_at;
  assert.equal(new Date(created).getDay(), 6);
});
