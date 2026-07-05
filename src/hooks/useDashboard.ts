import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";
import type { AnalysisResult, DashboardSummary } from "../types";

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => apiClient.get<DashboardSummary>("/api/dashboard/summary"),
  });
}

export function useHighRiskList() {
  return useQuery({
    queryKey: ["dashboard", "high-risk"],
    queryFn: () => apiClient.get<AnalysisResult[]>("/api/dashboard/high-risk"),
  });
}
