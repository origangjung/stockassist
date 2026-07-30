import assert from "node:assert/strict";
import { test } from "node:test";

import {
  readStoredItems,
  toggleStoredSymbol,
  writeStoredItems,
} from "./browser-watchlist.ts";

const stock = (symbol, name = symbol) => ({ symbol, name });

test("puts a new symbol first and removes it on the next toggle", () => {
  const initial = [stock("005930"), stock("AAPL")];
  const added = toggleStoredSymbol(initial, stock("NVDA"), 20);
  assert.equal(added.added, true);
  assert.deepEqual(added.items.map((item) => item.symbol), ["NVDA", "005930", "AAPL"]);

  const removed = toggleStoredSymbol(added.items, stock("005930"), 20);
  assert.equal(removed.added, false);
  assert.deepEqual(removed.items.map((item) => item.symbol), ["NVDA", "AAPL"]);
});

test("keeps the configured watchlist limit", () => {
  const result = toggleStoredSymbol([stock("A"), stock("B")], stock("C"), 2);
  assert.deepEqual(result.items.map((item) => item.symbol), ["C", "A"]);
});

test("falls back safely when browser storage is malformed or unavailable", () => {
  const malformedStorage = { getItem: () => "not-json", setItem: () => {} };
  assert.deepEqual(readStoredItems(malformedStorage, "watchlist", (value) => typeof value === "object" && value !== null, 20), {
    items: [],
    persisted: false,
  });

  const blockedStorage = {
    getItem: () => "[]",
    setItem: () => { throw new Error("blocked"); },
  };
  assert.equal(writeStoredItems(blockedStorage, "watchlist", [stock("005930")]), false);
});
