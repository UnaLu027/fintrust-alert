import { useQuery } from "@tanstack/react-query";
import { financialApiUrl } from "../lib/financialApi";
import type { FrontendAnalysisSnapshot } from "../types";

async function fetchPersistedFinancialAnalysis(
  ticker: string,
): Promise<FrontendAnalysisSnapshot | null> {
  const response = await fetch(
    financialApiUrl(`/api/v1/financial/companies/${encodeURIComponent(ticker)}/analysis/latest`),
    { headers: { Accept: "application/json" } },
  );
  if (response.status === 404) {
    return null;
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(body?.detail ?? "無法取得最新財報分析快照");
  }
  return body as FrontendAnalysisSnapshot;
}

export function usePersistedFinancialAnalysis(ticker: string) {
  return useQuery({
    queryKey: ["persisted-financial-analysis", ticker],
    queryFn: () => fetchPersistedFinancialAnalysis(ticker),
    enabled: Boolean(ticker),
    retry: 1,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: true,
  });
}
