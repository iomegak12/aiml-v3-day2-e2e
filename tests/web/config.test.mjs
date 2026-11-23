// Unit tests for web/site/js/config.js
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  API_PREDICT_PATH, DEFAULT_THEME, ENUMS, FIELD_LABELS, FIELD_LIMITS, FIXED_ETA_HOURS,
  HISTORY_MAX, KNOWN_PRODUCTS, THEMES,
} from "../../web/site/js/config.js";

test("fixed ETA per severity matches the business baseline", () => {
  assert.deepEqual({ ...FIXED_ETA_HOURS }, { S1: 4, S2: 24, S3: 48, S4: 72 });
});

test("enums and limits mirror TicketIn", () => {
  assert.deepEqual([...ENUMS.severity], ["S1", "S2", "S3", "S4"]);
  assert.deepEqual([...ENUMS.customer_tier], ["Platinum", "Gold", "Silver"]);
  assert.deepEqual([...ENUMS.region], ["AMER", "EMEA", "APJC"]);
  assert.deepEqual([...ENUMS.channel], ["Email", "Phone", "Portal"]);
  assert.deepEqual({ ...FIELD_LIMITS.devices_affected }, { min: 1, max: 1000, integer: true });
  assert.deepEqual({ ...FIELD_LIMITS.software_version_months }, { min: 0, max: 240, integer: true });
  assert.deepEqual({ ...FIELD_LIMITS.prior_tickets_90d }, { min: 0, max: 100, integer: true });
  assert.deepEqual({ ...FIELD_LIMITS.engineer_experience_years }, { min: 0, max: 50, optional: true });
  assert.deepEqual({ ...FIELD_LIMITS.first_response_minutes }, { min: 0, max: 10080, optional: true });
  assert.deepEqual({ ...FIELD_LIMITS.product_family }, { minLength: 1, maxLength: 50 });
});

test("every payload field has a label", () => {
  for (const field of [...Object.keys(ENUMS), ...Object.keys(FIELD_LIMITS), "created_at"]) {
    assert.ok(FIELD_LABELS[field], field);
  }
});

test("NetCore light and dark themes, light by default", () => {
  assert.deepEqual(THEMES.map((t) => t.id), ["netcore-light", "netcore-dark"]);
  assert.equal(DEFAULT_THEME, "netcore-light");
});

test("other constants", () => {
  assert.equal(API_PREDICT_PATH, "/api/v1/predictions");
  assert.equal(HISTORY_MAX, 20);
  assert.equal(KNOWN_PRODUCTS.length, 5);
  assert.ok(Object.isFrozen(FIXED_ETA_HOURS) && Object.isFrozen(FIELD_LIMITS));
});
