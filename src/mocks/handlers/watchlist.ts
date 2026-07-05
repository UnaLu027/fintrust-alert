import { http, HttpResponse, delay } from "msw";
import { unauthorized, userFromRequest } from "../authHelper";
import { watchlistOf } from "../db";
import type {
  AlertFrequency,
  AlertTypePref,
} from "../../types";

interface WatchlistUpdatePayload {
  watchedCompanies: string[];
  watchedIndustries: string[];
  watchedKeywords: string[];
  alertFrequency: AlertFrequency;
  alertTypes: AlertTypePref[];
}

export const watchlistHandlers = [
  http.get("/api/watchlist", async ({ request }) => {
    const user = userFromRequest(request);
    if (!user) return unauthorized();
    await delay(200);
    return HttpResponse.json({
      items: watchlistOf(user),
      alertFrequency: user.alertFrequency,
      alertTypes: user.alertTypes,
    });
  }),

  http.put("/api/watchlist", async ({ request }) => {
    const user = userFromRequest(request);
    if (!user) return unauthorized();
    const body = (await request.json()) as WatchlistUpdatePayload;
    await delay(300);

    user.watchedCompanies = body.watchedCompanies;
    user.watchedIndustries = body.watchedIndustries;
    user.watchedKeywords = body.watchedKeywords;
    user.alertFrequency = body.alertFrequency;
    user.alertTypes = body.alertTypes;

    return HttpResponse.json({
      items: watchlistOf(user),
      alertFrequency: user.alertFrequency,
      alertTypes: user.alertTypes,
    });
  }),
];
