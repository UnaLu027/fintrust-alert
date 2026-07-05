import type {
  AnalysisType,
  RiskLevel,
  SourceType,
  VerificationStatus,
} from "./analysis";

export interface HistoryRecord {
  id: string;
  userId: string;
  queryContent: string;
  dataSources: SourceType[];
  analysisType: AnalysisType;
  classification: VerificationStatus;
  riskLevel: RiskLevel;
  verificationStatus: VerificationStatus;
  analyzedAt: string;
  analysisId: string;
  isTracked: boolean;
}
