// Unit tests for web/site/js/history.js (fake storage)
import { test } from "node:test";
import assert from "node:assert/strict";

import { createHistory, formatTicketId } from "../../web/site/js/history.js";

function memoryStorage() {
  const data = new Map();
  return {
    getItem: (k) => (data.has(k) ? data.get(k) : null),
    setItem: (k, v) => data.set(k, String(v)),
    raw: data,
  };
}

const throwingStorage = {
  getItem() { throw new Error("blocked"); },
  setItem() { throw new Error("blocked"); },
};

test("ids increment and newest comes first", () => {
  const h = createHistory(memoryStorage());
  assert.equal(h.add({ eta: 1 }).id, "WEB-0001");
  assert.equal(h.add({ eta: 2 }).id, "WEB-0002");
  assert.deepEqual(h.list().map((e) => e.id), ["WEB-0002", "WEB-0001"]);
});

test("persists across instances with the same storage", () => {
  const storage = memoryStorage();
  createHistory(storage).add({ eta: 1 });
  assert.equal(createHistory(storage).list().length, 1);
});

test("capped at max entries", () => {
  const h = createHistory(memoryStorage(), { max: 3 });
  for (let i = 0; i < 5; i += 1) h.add({ i });
  assert.deepEqual(h.list().map((e) => e.i), [4, 3, 2]);
});

test("clear empties the list but ids keep counting", () => {
  const h = createHistory(memoryStorage());
  h.add({}); h.add({});
  h.clear();
  assert.deepEqual(h.list(), []);
  assert.equal(h.add({}).id, "WEB-0003");
});

test("corrupt JSON gives an empty list", () => {
  const storage = memoryStorage();
  storage.setItem("netcore-tac-history", "{not json");
  assert.deepEqual(createHistory(storage).list(), []);
});

test("throwing or missing storage falls back to memory", () => {
  for (const storage of [throwingStorage, null, undefined]) {
    const h = createHistory(storage);
    h.add({ eta: 1 });
    assert.equal(h.list().length, 1);
  }
});

test("formatTicketId pads to four digits", () => {
  assert.equal(formatTicketId(7), "WEB-0007");
  assert.equal(formatTicketId(12345), "WEB-12345");
});
