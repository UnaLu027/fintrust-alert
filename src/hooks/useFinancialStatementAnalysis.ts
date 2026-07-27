import { useQuery } from "@tanstack/react-query";
import { financialApiUrl } from "../lib/financialApi";
import type { FinancialStatementAnalysisReport } from "../types";

async function fetchFinancialAnalysis(
  ticker: string,
): Promise<FinancialStatementAnalysisReport> {
  const response = await fetch(
    financialApiUrl(
      `/api/v1/financial/statements/${encodeURIComponent(ticker)}/analyze`,
    ),
    { headers: { Accept: "application/json" } },
  );
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const message = body?.detail ?? "財報規則引擎暫時無法取得資料";
    throw new Error(message);
  }
  return body as FinancialStatementAnalysisReport;
}

export function useFinancialStatementAnalysis(ticker: string) {
  return useQuery({
    queryKey: ["financial-statement-analysis", ticker],
    queryFn: () => fetchFinancialAnalysis(ticker),
    enabled: false,
    retry: 1,
  });
}
