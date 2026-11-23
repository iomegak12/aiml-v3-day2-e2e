// "Registered this session" list, kept in sessionStorage (in-memory fallback if unavailable).

import { HISTORY_MAX, HISTORY_STORAGE_KEY } from "./config.js";

/** 1 -> "WEB-0001" */
export function formatTicketId(seq) {
  return `WEB-${String(seq).padStart(4, "0")}`;
}

function isState(value) {
  return value && Number.isInteger(value.seq) && value.seq >= 0 && Array.isArray(value.items);
}

/**
 * @param {Storage|null|undefined} storage e.g. window.sessionStorage (may be null or throw)
 * @param {{key?: string, max?: number}} [options]
 */
export function createHistory(storage, { key = HISTORY_STORAGE_KEY, max = HISTORY_MAX } = {}) {
  let memory = { seq: 0, items: [] };

  function read() {
    try {
      const raw = storage?.getItem(key);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (isState(parsed)) return parsed;
      }
    } catch {
      /* storage blocked or corrupt JSON: use memory */
    }
    return memory;
  }

  function write(state) {
    memory = state;
    try {
      storage?.setItem(key, JSON.stringify(state));
    } catch {
      /* quota exceeded or storage blocked: memory only */
    }
  }

  return {
    /** Newest first. */
    list() {
      return read().items.slice();
    },
    /** Add an entry; returns it with its new id. */
    add(entry) {
      const state = read();
      const seq = state.seq + 1;
      const item = { id: formatTicketId(seq), ...entry };
      write({ seq, items: [item, ...state.items].slice(0, max) });
      return item;
    },
    /** Empty the list; ids keep counting for the rest of the session. */
    clear() {
      write({ seq: read().seq, items: [] });
    },
  };
}
