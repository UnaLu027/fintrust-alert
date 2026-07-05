import { http, HttpResponse, delay } from "msw";
import { db } from "../db";
import { unauthorized, userFromRequest } from "../authHelper";

export const analysisHandlers = [
  http.get("/api/analysis/:id", async ({ request, params }) => {
    if (!userFromRequest(request)) return unauthorized();
    await delay(200);
    const analysis = db.analyses.find((a) => a.id === params.id);
    if (!analysis) {
      return HttpResponse.json(
        { error: { code: "not_found", message: "找不到此分析結果" } },
        { status: 404 },
      );
    }
    return HttpResponse.json(analysis);
  }),
];
