import { http, HttpResponse, delay } from "msw";
import { db } from "../db";
import { unauthorized, userFromRequest } from "../authHelper";
import { dashboardHighRiskIds, dashboardSummary } from "../fixtures/dashboardStats";

export const dashboardHandlers = [
  http.get("/api/dashboard/summary", async ({ request }) => {
    if (!userFromRequest(request)) return unauthorized();
    await delay(200);
    return HttpResponse.json(dashboardSummary);
  }),

  http.get("/api/dashboard/high-risk", async ({ request }) => {
    if (!userFromRequest(request)) return unauthorized();
    await delay(250);
    const items = dashboardHighRiskIds
      .map((id) => db.analyses.find((a) => a.id === id))
      .filter((a) => a !== undefined);
    return HttpResponse.json(items);
  }),
];
