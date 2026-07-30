export interface StockSearchItem {
  aliases?: readonly string[];
  name: string;
  symbol: string;
}

export type StockSearchMatchKind = "name" | "symbol" | "alias";

export interface StockSearchMatch<T extends StockSearchItem> {
  kind: StockSearchMatchKind;
  stock: T;
}

export function normalizeStockSearchText(value: string): string {
  return value.replace(/\s+/g, "").toLocaleUpperCase("ko-KR");
}

function matchesSearchText(stock: StockSearchItem, query: string, exact: boolean): boolean {
  return [stock.name, stock.symbol, ...(stock.aliases ?? [])].some((candidate) => {
    const normalizedCandidate = normalizeStockSearchText(candidate);
    return exact ? normalizedCandidate === query : normalizedCandidate.includes(query);
  });
}

function matchKind(stock: StockSearchItem, query: string): StockSearchMatchKind | undefined {
  const candidates: Array<[StockSearchMatchKind, string]> = [
    ["symbol", stock.symbol],
    ["name", stock.name],
    ...(stock.aliases ?? []).map((alias) => ["alias", alias] as [StockSearchMatchKind, string]),
  ];
  return candidates.find(([, candidate]) => normalizeStockSearchText(candidate).includes(query))?.[0];
}

function matchRank(stock: StockSearchItem, kind: StockSearchMatchKind, query: string): number {
  const candidate = kind === "symbol"
    ? stock.symbol
    : kind === "name"
      ? stock.name
      : (stock.aliases ?? []).find((alias) => normalizeStockSearchText(alias).includes(query)) ?? "";
  const normalizedCandidate = normalizeStockSearchText(candidate);
  if (normalizedCandidate === query) return 0;
  if (normalizedCandidate.startsWith(query)) return kind === "symbol" ? 1 : 2;
  return kind === "symbol" ? 3 : kind === "name" ? 4 : 5;
}

export function findStockByExactMatch<T extends StockSearchItem>(
  stocks: readonly T[],
  input: string,
): T | undefined {
  const query = normalizeStockSearchText(input);
  if (!query) return undefined;
  return stocks.find((stock) => matchesSearchText(stock, query, true));
}

export function filterStocksBySearch<T extends StockSearchItem>(
  stocks: readonly T[],
  input: string,
  limit = 5,
): T[] {
  const query = normalizeStockSearchText(input);
  const maximum = Math.max(0, Math.floor(limit));
  if (maximum === 0) return [];
  if (!query) return stocks.slice(0, maximum);
  return stocks.filter((stock) => matchesSearchText(stock, query, false)).slice(0, maximum);
}

export function findSimilarStockMatches<T extends StockSearchItem>(
  stocks: readonly T[],
  input: string,
  limit = 6,
): Array<StockSearchMatch<T>> {
  const query = normalizeStockSearchText(input);
  const maximum = Math.max(0, Math.floor(limit));
  if (maximum === 0 || !query) return [];
  return stocks
    .map((stock, index) => {
      const kind = matchKind(stock, query);
      return kind ? { index, match: { kind, stock }, rank: matchRank(stock, kind, query) } : undefined;
    })
    .filter((candidate): candidate is { index: number; match: StockSearchMatch<T>; rank: number } => candidate !== undefined)
    .sort((left, right) => left.rank - right.rank || left.index - right.index)
    .slice(0, maximum)
    .map(({ match }) => match);
}
