import { http, HttpResponse, delay } from "msw";
import { unauthorized, userFromRequest } from "../authHelper";
import type { VerifyRequestPayload } from "../../types";

/**
 * Mock matcher: maps free-text input to one of the 4 canned demo analyses so
 * the quick-verify flow always lands on a coherent, fully-populated result
 * page instead of an empty placeholder.
 */
function matchDemoAnalysisId(payload: VerifyRequestPayload): string {
  const text = [payload.keyword, payload.company, payload.ticker, payload.xUrl, payload.yahooUrl]
    .filter(Boolean)
    .join(" ");

  if (/暴跌|內線|假訊息|爆料/.test(text)) return "demo-tsmc-crash-rumor";
  if (/鴻海|2317|不一致|分歧/.test(text)) return "demo-multi-source-conflict";
  if (/法說|公告|重大訊息|官方/.test(text)) return "demo-mops-confirmed";
  return "demo-q2-revenue-surge";
}

export const verifyHandlers = [
  http.post("/api/verify/analyze", async ({ request }) => {
    if (!userFromRequest(request)) return unauthorized();
    const payload = (await request.json()) as VerifyRequestPayload;
    await delay(600);
    return HttpResponse.json({ analysisId: matchDemoAnalysisId(payload) });
  }),
];
