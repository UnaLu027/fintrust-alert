export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

export interface DashboardSummary {
  todayAnalyzedCount: number;
  highRiskCount: number;
  pendingVerificationCount: number;
  sourceInconsistentCount: number;
  officialConfirmedCount: number;
}

export interface VerifyRequestPayload {
  claimText?: string;
  keyword?: string;
  company?: string;
  ticker?: string;
  yahooUrl?: string;
  xUrl?: string;
  dateFrom?: string;
  dateTo?: string;
  sources: ("x" | "yahoo" | "mops")[];
  analysisTypes: (
    | "authenticity_check"
    | "exaggeration_detection"
    | "investment_inducement_risk"
    | "multi_source_verification"
    | "financial_statement_verification"
    | "full_analysis"
  )[];
}

export interface VerifyResponse {
  analysisId: string;
}
