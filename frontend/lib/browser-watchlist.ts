/** browser-watchlist 파일은 프론트 타입 계약과 API client 기능을 담당한다. */

export interface BrowserStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

/** SymbolItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface SymbolItem {
  symbol: string;
}

/** StoredItemsResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface StoredItemsResult<T> {
  items: T[];
  persisted: boolean;
}

/** `readStoredItems`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function readStoredItems<T>(
  storage: BrowserStorage,
  key: string,
  isValid: (value: unknown) => value is T,
  limit: number,
): StoredItemsResult<T> {
  try {
    const parsed = JSON.parse(storage.getItem(key) ?? "[]") as unknown;
    if (!Array.isArray(parsed)) return { items: [], persisted: true };
    return { items: parsed.filter(isValid).slice(0, limit), persisted: true };
  } catch {
    return { items: [], persisted: false };
  }
}

/** `writeStoredItems`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function writeStoredItems<T>(storage: BrowserStorage, key: string, items: readonly T[]): boolean {
  try {
    storage.setItem(key, JSON.stringify(items));
    return true;
  } catch {
    return false;
  }
}

/** `toggleStoredSymbol`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function toggleStoredSymbol<T extends SymbolItem>(
  items: readonly T[],
  item: T,
  limit: number,
): { items: T[]; added: boolean } {
  const exists = items.some((current) => current.symbol === item.symbol);
  return {
    added: !exists,
    items: exists
      ? items.filter((current) => current.symbol !== item.symbol)
      : [item, ...items.filter((current) => current.symbol !== item.symbol)].slice(0, limit),
  };
}
