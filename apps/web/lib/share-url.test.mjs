import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

import { stockResultUrl } from "./share-url.ts";

const originalWindow = Object.getOwnPropertyDescriptor(globalThis, "window");

function setLocation({ origin = "http://localhost:3000", pathname, search = "", hash = "" }) {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { location: { origin, pathname, search, hash } },
    writable: true,
  });
}

afterEach(() => {
  if (originalWindow) {
    Object.defineProperty(globalThis, "window", originalWindow);
    return;
  }
  delete globalThis.window;
});

test("normalizes a valid symbol into a minimal share URL", () => {
  setLocation({ pathname: "/" });

  assert.equal(stockResultUrl("  aapl "), "http://localhost:3000/?symbol=AAPL");
});

test("drops the current query and hash from a share URL", () => {
  setLocation({ pathname: "/research", search: "?admin_token=hidden", hash: "#private" });

  assert.equal(stockResultUrl("005930"), "http://localhost:3000/research?symbol=005930");
});

test("does not put malformed symbols into a share URL", () => {
  setLocation({ pathname: "/" });

  assert.equal(stockResultUrl("AAPL?private=value"), "http://localhost:3000/");
  assert.equal(stockResultUrl("THIS-SYMBOL-IS-TOO-LONG"), "http://localhost:3000/");
});
