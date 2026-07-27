import { useQuery } from "@tanstack/react-query";
import { financialApiUrl } from "../lib/financialApi";
import type { HistoricalFinancialAnalysisReport } from "../types";

async function fetchHistoricalFinancialAnalysis(
  ticker: string,
  years: number,
): Promise<HistoricalFinancialAnalysisReport> {
  const params = new URLSearchParams({ years: String(years) });
  const response = await fetch(
    financialApiUrl(
      `/api/v1/financial/statements/${encodeURIComponent(ticker)}/history?${params}`,
    ),
    { headers: { Accept: "application/json" } },
  );
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const message = body?.detail ?? "MOPS 歷史財報暫時無法取得";
    throw new Error(message);
  }
  return body as HistoricalFinancialAnalysisReport;
}

export function useHistoricalFinancialAnalysis(ticker: string, years: number) {
  return useQuery({
    queryKey: ["historical-financial-analysis", ticker, years],
    queryFn: () => fetchHistoricalFinancialAnalysis(ticker, years),
    enabled: false,
    retry: 0,
    staleTime: 30 * 60 * 1000,
  });
}
