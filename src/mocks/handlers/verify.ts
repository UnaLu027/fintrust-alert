import { http, HttpResponse, delay } from "msw";
import { unauthorized, userFromRequest } from "../authHelper";
import type { VerifyRequestPayload } from "../../types";

/**
 * Mock matcher: maps free-text input to coherent demo analyses. The financial
 * route proves the frontend/API contract before MOPS XBRL ingestion is enabled.
 */
function matchDemoAnalysisId(payload: VerifyRequestPayload): string {
  const text = [
    payload.claimText,
    payload.keyword,
    payload.company,
    payload.ticker,
    payload.xUrl,
    payload.yahooUrl,
  ]
    .filter(Boolean)
    .join(" ");

  const requestsFinancialEvidence =
    payload.analysisTypes.includes("financial_statement_verification") ||
    /營收|毛利率|營業利益率|淨利|EPS|財報|年增|季增|百分點|聯發科|2454/.test(text);

  if (requestsFinancialEvidence) return "demo-semiconductor-financial-evidence";
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
