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
  | "incomplete_information"
  | "financial_statement_mismatch";

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
  | "financial_statement_verification"
  | "full_analysis";

export type FinancialVerificationVerdict =
  | "supported"
  | "partially_supported"
  | "contradicted"
  | "insufficient_evidence"
  | "not_applicable";

export type FinancialClaimDirection =
  | "increase"
  | "decrease"
  | "higher_than"
  | "lower_than"
  | "equal"
  | "unspecified";

export interface ExtractedFinancialClaim {
  id: string;
  originalText: string;
  companyName?: string;
  ticker?: string;
  semiconductorSubindustry?: string;
  metric?: string;
  period?: string;
  comparisonPeriod?: string;
  direction: FinancialClaimDirection;
  claimedValue?: number;
  claimedChangePercent?: number;
  unit?: string;
  extractionConfidence: number;
}

export interface OfficialFinancialEvidence {
  id: string;
  sourceName: string;
  sourceUrl: string;
  sourceKind: "mops_xbrl" | "twse_openapi" | "mvp_fixture";
  statementType: "income_statement" | "balance_sheet" | "cash_flow" | "monthly_revenue";
  metric: string;
  period: string;
  comparisonPeriod?: string;
  currentValue?: number;
  comparisonValue?: number;
  unit: string;
  formula?: string;
  calculatedValue?: number;
  tolerance?: number;
  lastUpdatedAt: string;
  dataCoverage: string;
  isDemo: boolean;
}

export interface FinancialClaimVerification {
  claim: ExtractedFinancialClaim;
  verdict: FinancialVerificationVerdict;
  explanation: string;
  difference?: number;
  evidenceIds: string[];
}

export interface FinancialEvidenceResult {
  industry: "半導體";
  method: "claim_extraction_and_deterministic_recalculation";
  overallVerdict: FinancialVerificationVerdict;
  summary: string;
  claims: FinancialClaimVerification[];
  evidence: OfficialFinancialEvidence[];
  limitations: string[];
  generatedAt: string;
}

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
  financialEvidence?: FinancialEvidenceResult;
}
