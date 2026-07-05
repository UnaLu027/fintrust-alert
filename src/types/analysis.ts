export type RiskLevel = "low" | "medium" | "high";

export type VerificationStatus =
  | "pending"
  | "inconsistent"
  | "official_confirmed"
  | "suspected_false";

export type SourceType = "x" | "yahoo" | "mops";

export type RiskReasonCode =
  | "exaggerated_tone"
  | "insufficient_official_support"
  | "source_inconsistency"
  | "abnormal_social_spread"
  | "investment_inducement_risk"
  | "incomplete_information";

export interface RiskReason {
  code: RiskReasonCode;
  label: string;
  explanation: string;
}

export type SourceRelation = "supports" | "inconsistent" | "partially_related";

export type SourceStatusTag =
  | "official_confirmed"
  | "supportable"
  | "no_official_support"
  | "pending";

export interface SourceComparison {
  source: SourceType;
  hasContent: boolean;
  title?: string;
  summary?: string;
  handleOrOutlet?: string;
  publishedAt?: string;
  relationToOriginal?: SourceRelation;
  modelJudgment: string;
  riskTags?: string[];
  disclaimerText: string;
  statusTag: SourceStatusTag;
}

export type AnalysisType =
  | "authenticity_check"
  | "exaggeration_detection"
  | "investment_inducement_risk"
  | "multi_source_verification"
  | "full_analysis";

export interface AnalysisResult {
  id: string;
  title: string;
  classification: VerificationStatus;
  relatedTicker?: string;
  relatedCompany?: string;
  sources: SourceType[];
  analyzedAt: string;
  riskLevel: RiskLevel;
  riskScore: number;
  verificationStatus: VerificationStatus;
  hasOfficialSupport: boolean;
  modelJudgmentSummary: string;
  riskExplanationParagraph: string;
  riskReasons: RiskReason[];
  sourceComparisons: SourceComparison[];
  analysisTypesRequested: AnalysisType[];
}
