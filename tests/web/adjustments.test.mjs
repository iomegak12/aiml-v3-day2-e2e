// Unit tests for web/site/js/adjustments.js
import { test } from "node:test";
import assert from "node:assert/strict";

import { formatAdjustments } from "../../web/site/js/adjustments.js";

test("formats each clamped input with its label", () => {
  assert.deepEqual(formatAdjustments([
    { field: "engineer_experience_years", original: 35, used: 20 },
    { field: "first_response_minutes", original: 0, used: 2.2 },
    { field: "devices_affected", original: 200, used: 54 },
  ]), [
    "Engineer experience (years): 35 → 20",
    "First response (minutes): 0 → 2.2",
    "Devices affected: 200 → 54",
  ]);
});

test("rounds long decimals to one place", () => {
  assert.deepEqual(formatAdjustments([{ field: "first_response_minutes", original: 900.456, used: 800.4 }]),
    ["First response (minutes): 900.5 → 800.4"]);
});

test("empty, missing or malformed input gives no lines", () => {
  assert.deepEqual(formatAdjustments([]), []);
  assert.deepEqual(formatAdjustments(undefined), []);
  assert.deepEqual(formatAdjustments(null), []);
  assert.deepEqual(formatAdjustments([null, { field: 3 }, { field: "x" }]), []);
});

test("unknown field keeps its API name", () => {
  assert.deepEqual(formatAdjustments([{ field: "new_field", original: 1, used: 2 }]), ["new_field: 1 → 2"]);
});
