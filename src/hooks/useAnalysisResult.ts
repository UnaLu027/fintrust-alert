import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";
import type { AnalysisResult } from "../types";

export function useAnalysisResult(id: string | undefined) {
  return useQuery({
    queryKey: ["analysis", id],
    queryFn: () => apiClient.get<AnalysisResult>(`/api/analysis/${id}`),
    enabled: Boolean(id),
  });
}
