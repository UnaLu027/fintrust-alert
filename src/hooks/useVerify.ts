import { useMutation } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";
import type { VerifyRequestPayload, VerifyResponse } from "../types";

export function useAnalyzeSubmit() {
  return useMutation({
    mutationFn: (payload: VerifyRequestPayload) =>
      apiClient.post<VerifyResponse>("/api/verify/analyze", payload),
  });
}
