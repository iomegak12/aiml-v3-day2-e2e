// Unit tests for web/site/js/payload.js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  formToPayload, toIsoDateTime, toNumber, toOptionalNumber, validatePayload,
} from "../../web/site/js/payload.js";

const SAMPLE = JSON.parse(readFileSync(new URL("../../data/sample_prediction_request.json", import.meta.url), "utf8"));

const FORM = {
  created_at: "2026-11-23T10:15", product_family: " Routers ", severity: "S2", customer_tier: "Gold",
  region: "EMEA", channel: "Phone", devices_affected: "4", software_version_months: "40",
  prior_tickets_90d: "1", engineer_experience_years: "6.5", first_response_minutes: "20",
};

test("form values become the sample request payload exactly", () => {
  assert.deepEqual(formToPayload(FORM), SAMPLE);
  assert.deepEqual(validatePayload(formToPayload(FORM)), {});
});

test("datetime-local gets seconds; other strings unchanged", () => {
  assert.equal(toIsoDateTime("2026-11-23T10:15"), "2026-11-23T10:15:00");
  assert.equal(toIsoDateTime("2026-11-23T10:15:30"), "2026-11-23T10:15:30");
  assert.equal(toIsoDateTime(""), "");
});

test("number conversions", () => {
  assert.ok(Number.isNaN(toNumber("")));
  assert.equal(toNumber(" 7 "), 7);
  assert.equal(toOptionalNumber(""), null);
  assert.equal(toOptionalNumber(undefined), null);
  assert.equal(toOptionalNumber("0"), 0);
});

test("blank optional numbers become null and stay valid", () => {
  const payload = formToPayload({ ...FORM, engineer_experience_years: "", first_response_minutes: " " });
  assert.equal(payload.engineer_experience_years, null);
  assert.equal(payload.first_response_minutes, null);
  assert.deepEqual(validatePayload(payload), {});
});

const invalid = [
  ["created_at", ""], ["created_at", "2026-02-30T10:00"], ["created_at", "yesterday"],
  ["product_family", ""], ["product_family", "x".repeat(51)],
  ["severity", "S5"], ["customer_tier", "Bronze"], ["region", "LATAM"], ["channel", "Fax"],
  ["devices_affected", "0"], ["devices_affected", "1001"], ["devices_affected", "2.5"], ["devices_affected", ""],
  ["software_version_months", "-1"], ["software_version_months", "241"],
  ["prior_tickets_90d", "101"],
  ["engineer_experience_years", "51"], ["engineer_experience_years", "abc"],
  ["first_response_minutes", "-0.1"], ["first_response_minutes", "10081"],
];
for (const [field, value] of invalid) {
  test(`invalid ${field}=${JSON.stringify(value)} is reported for that field only`, () => {
    const errors = validatePayload(formToPayload({ ...FORM, [field]: value }));
    assert.deepEqual(Object.keys(errors), [field]);
    assert.match(errors[field], /\S/);
  });
}

test("boundary values are valid", () => {
  const edge = { ...FORM, devices_affected: "1000", software_version_months: "0", prior_tickets_90d: "100",
                 engineer_experience_years: "50", first_response_minutes: "10080", product_family: "x".repeat(50) };
  assert.deepEqual(validatePayload(formToPayload(edge)), {});
});
