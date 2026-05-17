import { openDB, type IDBPDatabase } from "idb";

interface FatehSchema {
  recent_searches: { q: string; ts: number };
}

let _db: IDBPDatabase<unknown> | null = null;

async function getDb() {
  if (_db) return _db;
  _db = await openDB("fateh_support", 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains("recent_searches")) {
        db.createObjectStore("recent_searches", { keyPath: "q" });
      }
    },
  });
  return _db;
}

export async function rememberSearch(query: string): Promise<void> {
  const q = query.trim();
  if (!q) return;
  const db = await getDb();
  await db.put("recent_searches", { q, ts: Date.now() });
}

export async function recentSearches(limit = 8): Promise<string[]> {
  const db = await getDb();
  const all = (await db.getAll("recent_searches")) as FatehSchema["recent_searches"][];
  return all
    .sort((a, b) => b.ts - a.ts)
    .slice(0, limit)
    .map((r) => r.q);
}

export async function clearRecent(): Promise<void> {
  const db = await getDb();
  await db.clear("recent_searches");
}
