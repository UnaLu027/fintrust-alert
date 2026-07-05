import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";
import type { PushAlert } from "../types";

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: () => apiClient.get<PushAlert[]>("/api/alerts"),
  });
}
