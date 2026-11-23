// Unit tests for web/site/js/api.js (fake fetch; no network)
import { test } from "node:test";
import assert from "node:assert/strict";

import { errorKind, parseRetryAfter, predict, toFieldErrors } from "../../web/site/js/api.js";

const PROBLEM = "application/problem+json";

function respond(status, body, headers = {}) {
  const text = typeof body === "string" ? body : JSON.stringify(body);
  return new Response(text, { status, headers: { "Content-Type": "application/json", ...headers } });
}

function fakeFetch(response, calls = []) {
  return async (url, init) => {
    calls.push({ url, init });
    return typeof response === "function" ? response(init) : response;
  };
}

test("200 returns data and the X-Request-ID", async () => {
  const calls = [];
  const body = { predicted_hours: 32.5, model_version: "0.3.0", request_id: "rid-body" };
  const result = await predict({ a: 1 }, { fetchImpl: fakeFetch(respond(200, body, { "X-Request-ID": "rid-1" }), calls) });
  assert.deepEqual(result, { ok: true, data: body, requestId: "rid-1" });
  assert.equal(calls[0].url, "/api/v1/predictions");
  assert.equal(calls[0].init.method, "POST");
  assert.equal(calls[0].init.headers["Content-Type"], "application/json");
  assert.equal(calls[0].init.body, JSON.stringify({ a: 1 }));
});

test("request_id falls back to the body", async () => {
  const result = await predict({}, { fetchImpl: fakeFetch(respond(200, { request_id: "rid-b" })) });
  assert.equal(result.requestId, "rid-b");
});

test("422 maps errors to fields", async () => {
  const problem = { status: 422, request_id: "r", errors: [
    { field: "severity", message: "bad" }, { field: "severity", message: "second" }, { field: "body", message: "x" }] };
  const result = await predict({}, { fetchImpl: fakeFetch(respond(422, problem, { "Content-Type": PROBLEM })) });
  assert.equal(result.ok, false);
  assert.equal(result.kind, "validation");
  assert.deepEqual(result.fieldErrors, { severity: "bad", body: "x" });
  assert.equal(result.requestId, "r");
});

test("429 reads Retry-After", async () => {
  const result = await predict({}, { fetchImpl: fakeFetch(respond(429, { status: 429 }, { "Retry-After": "30" })) });
  assert.equal(result.kind, "rate-limited");
  assert.equal(result.retryAfter, 30);
});

test("503, 502, 504 and 500 kinds", async () => {
  for (const [status, kind] of [[503, "not-ready"], [502, "unavailable"], [504, "unavailable"], [500, "server"]]) {
    const result = await predict({}, { fetchImpl: fakeFetch(respond(status, { status })) });
    assert.equal(result.kind, kind, String(status));
    assert.equal(result.status, status);
  }
});

test("non-JSON error body still gives a result", async () => {
  const result = await predict({}, { fetchImpl: fakeFetch(respond(502, "<html>Bad Gateway</html>")) });
  assert.equal(result.kind, "unavailable");
  assert.equal(result.problem, null);
  assert.deepEqual(result.fieldErrors, {});
});

test("network failure and timeout", async () => {
  const network = await predict({}, { fetchImpl: async () => { throw new TypeError("Failed to fetch"); } });
  assert.equal(network.kind, "network");

  const hanging = (url, init) => new Promise((_, reject) => {
    init.signal.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
  });
  const timeout = await predict({}, { fetchImpl: hanging, timeoutMs: 10 });
  assert.equal(timeout.kind, "timeout");
});

test("helpers", () => {
  assert.equal(errorKind(418), "server");
  assert.equal(parseRetryAfter("12"), 12);
  assert.equal(parseRetryAfter(null), 0);
  assert.equal(parseRetryAfter("soon"), 0);
  assert.deepEqual(toFieldErrors(null), {});
});
