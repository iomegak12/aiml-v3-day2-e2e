// Unit tests for web/site/js/eta.js
import { test } from "node:test";
import assert from "node:assert/strict";

import { compareWithFixed, formatDuration, formatHours } from "../../web/site/js/eta.js";

test("formatHours drops a trailing .0", () => {
  assert.equal(formatHours(8), "8");
  assert.equal(formatHours(8.46), "8.5");
  assert.equal(formatHours(0.04), "0");
});

test("formatDuration boundaries", () => {
  const cases = [[0, "0 h"], [0.04, "0 h"], [16.3, "16.3 h"], [23.9, "23.9 h"], [23.96, "1 d"],
                 [24, "1 d"], [32.5, "1 d 8.5 h"], [47.97, "2 d"], [100, "4 d 4 h"], [-3, "0 h"]];
  for (const [hours, expected] of cases) assert.equal(formatDuration(hours), expected, String(hours));
});

test("compareWithFixed sign and label per severity", () => {
  assert.deepEqual(compareWithFixed("S2", 32.5), { fixed: 24, delta: 8.5, label: "+8.5 h vs fixed" });
  assert.deepEqual(compareWithFixed("S1", 4), { fixed: 4, delta: 0, label: "Same as fixed" });
  assert.deepEqual(compareWithFixed("S4", 35.7), { fixed: 72, delta: -36.3, label: "−36.3 h vs fixed" });
  assert.equal(compareWithFixed("S3", 59.5).fixed, 48);
});

test("unknown severity throws", () => {
  assert.throws(() => compareWithFixed("S9", 1), RangeError);
});
