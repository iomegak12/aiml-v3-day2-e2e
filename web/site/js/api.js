// Client for POST /api/v1/predictions (same origin, via NGINX) with RFC 9457 error handling.

import { API_PREDICT_PATH, REQUEST_TIMEOUT_MS } from "./config.js";

/** HTTP status -> error kind the UI reacts to. */
export function errorKind(status) {
  if (status === 422) return "validation";
  if (status === 429) return "rate-limited";
  if (status === 503) return "not-ready";
  if (status === 502 || status === 504) return "unavailable";
  return "server";
}

/** Retry-After in whole seconds (delta-seconds form); 0 when missing or invalid. */
export function parseRetryAfter(value) {
  const seconds = Number.parseInt(value ?? "", 10);
  return Number.isFinite(seconds) && seconds > 0 ? seconds : 0;
}

/** Problem details body, or null when the body is not JSON. */
export async function parseProblem(response) {
  try {
    const body = await response.json();
    return body && typeof body === "object" ? body : null;
  } catch {
    return null;
  }
}

/** problem.errors [{field, message}] -> {field: message} (first message per field). */
export function toFieldErrors(problem) {
  const result = {};
  for (const item of problem?.errors ?? []) {
    if (item && typeof item.field === "string" && !(item.field in result)) {
      result[item.field] = String(item.message ?? "Invalid value");
    }
  }
  return result;
}

function failure(kind, extra = {}) {
  return { ok: false, kind, status: 0, problem: null, fieldErrors: {}, retryAfter: 0, requestId: null, ...extra };
}

/**
 * Ask the API for a prediction.
 * @param {object} payload TicketIn body
 * @param {{fetchImpl?: typeof fetch, timeoutMs?: number}} [options]
 * @returns {Promise<{ok: true, data: object, requestId: string|null} | {ok: false, kind: string,
 *   status: number, problem: object|null, fieldErrors: Record<string,string>, retryAfter: number,
 *   requestId: string|null}>}
 */
export async function predict(payload, { fetchImpl = globalThis.fetch, timeoutMs = REQUEST_TIMEOUT_MS } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let response;
  try {
    response = await fetchImpl(API_PREDICT_PATH, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json, application/problem+json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
  } catch (error) {
    return failure(error?.name === "AbortError" ? "timeout" : "network");
  } finally {
    clearTimeout(timer);
  }

  const headerId = response.headers.get("X-Request-ID");
  if (response.ok) {
    const data = await parseProblem(response);   // same JSON parsing, success body
    if (!data) return failure("server", { status: response.status, requestId: headerId });
    return { ok: true, data, requestId: headerId ?? data.request_id ?? null };
  }

  const problem = await parseProblem(response);
  return failure(errorKind(response.status), {
    status: response.status,
    problem,
    fieldErrors: toFieldErrors(problem),
    retryAfter: parseRetryAfter(response.headers.get("Retry-After")),
    requestId: headerId ?? problem?.request_id ?? null,
  });
}
