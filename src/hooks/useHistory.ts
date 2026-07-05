import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";
import type { HistoryRecord } from "../types";

export function useHistory() {
  return useQuery({
    queryKey: ["history"],
    queryFn: () => apiClient.get<HistoryRecord[]>("/api/history"),
  });
}

export function useTrackHistoryItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.post<HistoryRecord>(`/api/history/${id}/track`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["history"] }),
  });
}

export function useDeleteHistoryItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<{ ok: boolean }>(`/api/history/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["history"] }),
  });
}
