import assert from "node:assert/strict";
import { test } from "node:test";

import {
  filterStocksBySearch,
  findStockByExactMatch,
  findSimilarStockMatches,
  normalizeStockSearchText,
} from "./stock-search.ts";

const stocks = [
  { symbol: "005930", name: "삼성전자", aliases: ["삼전", "samsung", "samsung electronics"] },
  { symbol: "AAPL", name: "Apple", aliases: ["애플"] },
  { symbol: "NVDA", name: "NVIDIA", aliases: ["엔비디아"] },
];

test("normalizes whitespace and case for Korean and US stock searches", () => {
  assert.equal(normalizeStockSearchText(" samsung electronics "), "SAMSUNGELECTRONICS");
  assert.equal(normalizeStockSearchText("삼 성 전 자"), "삼성전자");
});

test("finds exact names, aliases, and tickers", () => {
  assert.equal(findStockByExactMatch(stocks, "삼전")?.symbol, "005930");
  assert.equal(findStockByExactMatch(stocks, "samsung electronics")?.symbol, "005930");
  assert.equal(findStockByExactMatch(stocks, " aapl ")?.symbol, "AAPL");
  assert.equal(findStockByExactMatch(stocks, "애플")?.symbol, "AAPL");
  assert.equal(findStockByExactMatch(stocks, "없는 종목"), undefined);
});

test("filters partial matches while preserving the original order and limit", () => {
  assert.deepEqual(filterStocksBySearch(stocks, "samsung"), [stocks[0]]);
  assert.deepEqual(filterStocksBySearch(stocks, "", 2), [stocks[0], stocks[1]]);
  assert.deepEqual(filterStocksBySearch(stocks, "a", 1), [stocks[0]]);
  assert.deepEqual(filterStocksBySearch(stocks, "a", 0), []);
});

test("ranks similar matches and explains whether name, ticker, or alias matched", () => {
  assert.deepEqual(
    findSimilarStockMatches(stocks, "aapl").map(({ kind, stock }) => [kind, stock.symbol]),
    [["symbol", "AAPL"]],
  );
  assert.deepEqual(
    findSimilarStockMatches(stocks, "애").map(({ kind, stock }) => [kind, stock.symbol]),
    [["alias", "AAPL"]],
  );
  assert.deepEqual(
    findSimilarStockMatches(stocks, "n").map(({ kind, stock }) => [kind, stock.symbol]),
    [["symbol", "NVDA"], ["alias", "005930"]],
  );
});
