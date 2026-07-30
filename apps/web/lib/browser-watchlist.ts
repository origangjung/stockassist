export interface BrowserStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export interface SymbolItem {
  symbol: string;
}

export interface StoredItemsResult<T> {
  items: T[];
  persisted: boolean;
}

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

export function writeStoredItems<T>(storage: BrowserStorage, key: string, items: readonly T[]): boolean {
  try {
    storage.setItem(key, JSON.stringify(items));
    return true;
  } catch {
    return false;
  }
}

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
