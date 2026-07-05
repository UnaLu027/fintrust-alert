import type { RiskLevel, VerificationStatus } from "./analysis";

export type PushTemplateType =
  | "credibility_risk"
  | "pending_verification"
  | "source_inconsistent"
  | "official_update"
  | "personalized_digest";

export interface PushAlert {
  id: string;
  userId: string;
  templateType: PushTemplateType;
  title: string;
  relatedTarget: string;
  riskLevel: RiskLevel;
  verificationStatus: VerificationStatus;
  reason: string;
  message: string;
  createdAt: string;
  analysisId: string;
}
