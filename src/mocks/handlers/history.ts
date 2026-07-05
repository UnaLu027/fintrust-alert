import { http, HttpResponse, delay } from "msw";
import { db } from "../db";
import { unauthorized, userFromRequest } from "../authHelper";

export const historyHandlers = [
  http.get("/api/history", async ({ request }) => {
    const user = userFromRequest(request);
    if (!user) return unauthorized();
    await delay(250);
    const items = db.history
      .filter((h) => h.userId === user.id)
      .sort((a, b) => (a.analyzedAt < b.analyzedAt ? 1 : -1));
    return HttpResponse.json(items);
  }),

  http.post("/api/history/:id/track", async ({ request, params }) => {
    const user = userFromRequest(request);
    if (!user) return unauthorized();
    await delay(200);
    const record = db.history.find((h) => h.id === params.id && h.userId === user.id);
    if (!record) {
      return HttpResponse.json(
        { error: { code: "not_found", message: "找不到此分析紀錄" } },
        { status: 404 },
      );
    }
    record.isTracked = true;
    return HttpResponse.json(record);
  }),

  http.delete("/api/history/:id", async ({ request, params }) => {
    const user = userFromRequest(request);
    if (!user) return unauthorized();
    await delay(200);
    const index = db.history.findIndex((h) => h.id === params.id && h.userId === user.id);
    if (index === -1) {
      return HttpResponse.json(
        { error: { code: "not_found", message: "找不到此分析紀錄" } },
        { status: 404 },
      );
    }
    db.history.splice(index, 1);
    return HttpResponse.json({ ok: true });
  }),
];
