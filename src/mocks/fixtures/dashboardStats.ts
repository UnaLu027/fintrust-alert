import type { DashboardSummary } from "../../types";
import { demoAnalyses } from "./analyses";

export const dashboardSummary: DashboardSummary = {
  todayAnalyzedCount: 128,
  highRiskCount: 23,
  pendingVerificationCount: 41,
  sourceInconsistentCount: 7,
  officialConfirmedCount: 18,
};

/** dashboard "今日高風險資訊" list: risk >= medium, newest first */
export const dashboardHighRiskIds = demoAnalyses
  .filter((a) => a.riskLevel === "high" || a.riskLevel === "medium")
  .sort((a, b) => (a.analyzedAt < b.analyzedAt ? 1 : -1))
  .map((a) => a.id);
