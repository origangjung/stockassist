const STOCK_SYMBOL_PATTERN = /^[0-9A-Z.-]{1,16}$/;

/**
 * Build the smallest stable URL needed to reopen a stock result.
 * It intentionally drops existing query parameters and hashes so they are not
 * accidentally exposed when a user shares an analysis result.
 */
export function stockResultUrl(symbol: string): string {
  const url = new URL(window.location.pathname, window.location.origin);
  const normalizedSymbol = symbol.trim().toUpperCase();

  if (STOCK_SYMBOL_PATTERN.test(normalizedSymbol)) {
    url.searchParams.set("symbol", normalizedSymbol);
  }

  return url.toString();
}
