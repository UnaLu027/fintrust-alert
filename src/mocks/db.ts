import type { HistoryRecord, PushAlert, User, WatchlistItem } from "../types";
import { demoAnalyses } from "./fixtures/analyses";
import { demoHistoryRecords } from "./fixtures/historyRecords";
import { demoPushAlerts } from "./fixtures/pushAlerts";
import { demoPassword, demoUser } from "./fixtures/users";

/** In-memory mutable mock store, seeded from fixtures. Handlers read/write this. */
export const db = {
  users: [demoUser] as User[],
  passwords: new Map<string, string>([[demoUser.email, demoPassword]]),
  analyses: [...demoAnalyses],
  history: [...demoHistoryRecords] as HistoryRecord[],
  alerts: [...demoPushAlerts] as PushAlert[],
};

export function watchlistOf(user: User): WatchlistItem[] {
  const items: WatchlistItem[] = [];
  user.watchedCompanies.forEach((value, i) =>
    items.push({ id: `wl-company-${i}`, userId: user.id, type: "company", value }),
  );
  user.watchedIndustries.forEach((value, i) =>
    items.push({ id: `wl-industry-${i}`, userId: user.id, type: "industry", value }),
  );
  user.watchedKeywords.forEach((value, i) =>
    items.push({ id: `wl-keyword-${i}`, userId: user.id, type: "keyword", value }),
  );
  return items;
}

let idCounter = 1000;
export function nextId(prefix: string): string {
  idCounter += 1;
  return `${prefix}-${idCounter}`;
}
