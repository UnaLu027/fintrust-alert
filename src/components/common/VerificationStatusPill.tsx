import type { VerificationStatus } from "../../types";
import { verificationStatusLabels } from "../../content/copy";

const styles: Record<VerificationStatus, string> = {
  pending: "bg-brand-sky text-brand-blue border-brand-blue/20",
  inconsistent: "bg-risk-medium-bg text-risk-medium border-risk-medium/30",
  official_confirmed: "bg-risk-low-bg text-risk-low border-risk-low/30",
  suspected_false: "bg-risk-high-bg text-risk-high border-risk-high/30",
};

export function VerificationStatusPill({ status }: { status: VerificationStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}
    >
      {verificationStatusLabels[status]}
    </span>
  );
}
