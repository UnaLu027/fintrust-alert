import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";
import type { AlertFrequency, AlertTypePref, WatchlistItem } from "../types";

interface WatchlistResponse {
  items: WatchlistItem[];
  alertFrequency: AlertFrequency;
  alertTypes: AlertTypePref[];
}

export interface WatchlistUpdatePayload {
  watchedCompanies: string[];
  watchedIndustries: string[];
  watchedKeywords: string[];
  alertFrequency: AlertFrequency;
  alertTypes: AlertTypePref[];
}

export function useWatchlist() {
  return useQuery({
    queryKey: ["watchlist"],
    queryFn: () => apiClient.get<WatchlistResponse>("/api/watchlist"),
  });
}

export function useUpdateWatchlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: WatchlistUpdatePayload) =>
      apiClient.put<WatchlistResponse>("/api/watchlist", payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["watchlist"] }),
  });
}
