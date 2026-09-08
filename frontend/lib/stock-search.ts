/** stock-search 파일은 프론트 타입 계약과 API client 기능을 담당한다. */

export interface StockSearchItem {
  aliases?: readonly string[];
  name: string;
  symbol: string;
}

export type StockSearchMatchKind = "name" | "symbol" | "alias";

/** StockSearchMatch 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface StockSearchMatch<T extends StockSearchItem> {
  kind: StockSearchMatchKind;
  stock: T;
}

/** `normalizeStockSearchText`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function normalizeStockSearchText(value: string): string {
  return value.replace(/\s+/g, "").toLocaleUpperCase("ko-KR");
}

/** `editDistanceAtMostOne`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function editDistanceAtMostOne(left: string, right: string): boolean {
  if (Math.abs(left.length - right.length) > 1) return false;
  if (left === right) return true;
  if (left.length === right.length) {
    let differences = 0;
    for (let index = 0; index < left.length; index += 1) {
      if (left[index] !== right[index] && ++differences > 1) return false;
    }
    return true;
  }
  const [shorter, longer] = left.length < right.length ? [left, right] : [right, left];
  let shortIndex = 0;
  let longIndex = 0;
  let skipped = false;
  while (shortIndex < shorter.length && longIndex < longer.length) {
    if (shorter[shortIndex] === longer[longIndex]) {
      shortIndex += 1;
      longIndex += 1;
      continue;
    }
    if (skipped) return false;
    skipped = true;
    longIndex += 1;
  }
  return true;
}

/** `isTolerantKoreanMatch`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function isTolerantKoreanMatch(candidate: string, query: string): boolean {
  if (query.length < 2 || !/[가-힣]/.test(query)) return false;
  if (!/[가-힣]/.test(candidate)) return false;
  for (let index = 0; index <= candidate.length - query.length; index += 1) {
    if (editDistanceAtMostOne(candidate.slice(index, index + query.length), query)) return true;
  }
  return false;
}

/** `matchesSearchText`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function matchesSearchText(stock: StockSearchItem, query: string, exact: boolean): boolean {
  return [stock.name, stock.symbol, ...(stock.aliases ?? [])].some((candidate) => {
    const normalizedCandidate = normalizeStockSearchText(candidate);
    return exact
      ? normalizedCandidate === query
      : normalizedCandidate.includes(query) || isTolerantKoreanMatch(normalizedCandidate, query);
  });
}

/** `matchKind`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function matchKind(stock: StockSearchItem, query: string): StockSearchMatchKind | undefined {
  const candidates: Array<[StockSearchMatchKind, string]> = [
    ["symbol", stock.symbol],
    ["name", stock.name],
    ...(stock.aliases ?? []).map((alias) => ["alias", alias] as [StockSearchMatchKind, string]),
  ];
  return candidates.find(([, candidate]) => {
    const normalizedCandidate = normalizeStockSearchText(candidate);
    return normalizedCandidate.includes(query) || isTolerantKoreanMatch(normalizedCandidate, query);
  })?.[0];
}

/** `matchRank`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function matchRank(stock: StockSearchItem, kind: StockSearchMatchKind, query: string): number {
  const candidate = kind === "symbol"
    ? stock.symbol
    : kind === "name"
      ? stock.name
      : (stock.aliases ?? []).find((alias) => normalizeStockSearchText(alias).includes(query)) ?? "";
  const normalizedCandidate = normalizeStockSearchText(candidate);
  if (normalizedCandidate === query) return 0;
  if (normalizedCandidate.startsWith(query)) return kind === "symbol" ? 1 : 2;
  if (!normalizedCandidate.includes(query)) return 6;
  return kind === "symbol" ? 3 : kind === "name" ? 4 : 5;
}

/** `findStockByExactMatch`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function findStockByExactMatch<T extends StockSearchItem>(
  stocks: readonly T[],
  input: string,
): T | undefined {
  const query = normalizeStockSearchText(input);
  if (!query) return undefined;
  return stocks.find((stock) => matchesSearchText(stock, query, true));
}

/** `filterStocksBySearch`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
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

/** `findSimilarStockMatches`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function findSimilarStockMatches<T extends StockSearchItem>(
  stocks: readonly T[],
  input: string,
  limit = 6,
): Array<StockSearchMatch<T>> {
  const query = normalizeStockSearchText(input);
  const maximum = Math.max(0, Math.floor(limit));
  if (maximum === 0 || !query) return [];
  const candidates = stocks
    .map((stock, index) => {
      const kind = matchKind(stock, query);
      return kind ? { index, match: { kind, stock }, rank: matchRank(stock, kind, query) } : undefined;
    })
    .filter((candidate): candidate is { index: number; match: StockSearchMatch<T>; rank: number } => candidate !== undefined);
  const hasDirectMatch = candidates.some(({ rank }) => rank < 6);
  return candidates
    .filter(({ rank }) => !hasDirectMatch || rank < 6)
    .sort((left, right) => left.rank - right.rank || left.index - right.index)
    .slice(0, maximum)
    .map(({ match }) => match);
}
