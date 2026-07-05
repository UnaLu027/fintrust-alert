import { http, HttpResponse, delay } from "msw";
import { db } from "../db";
import { unauthorized, userFromRequest } from "../authHelper";

export const alertsHandlers = [
  http.get("/api/alerts", async ({ request }) => {
    const user = userFromRequest(request);
    if (!user) return unauthorized();
    await delay(250);
    const items = db.alerts
      .filter((a) => a.userId === user.id)
      .sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));
    return HttpResponse.json(items);
  }),
];
