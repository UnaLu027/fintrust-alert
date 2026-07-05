import type { RiskLevel } from "../../types";
import { riskLevelLabel } from "../../content/riskExplanations";

const styles: Record<RiskLevel, string> = {
  low: "bg-risk-low-bg text-risk-low border-risk-low/30",
  medium: "bg-risk-medium-bg text-risk-medium border-risk-medium/30",
  high: "bg-risk-high-bg text-risk-high border-risk-high/30",
};

export function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[level]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      可信度風險：{riskLevelLabel[level]}
    </span>
  );
}
