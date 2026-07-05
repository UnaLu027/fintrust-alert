import type { RiskReason } from "../../types";

export function RiskReasonList({ reasons }: { reasons: RiskReason[] }) {
  if (reasons.length === 0) {
    return (
      <p className="text-sm text-brand-muted">目前未偵測到明顯風險原因。</p>
    );
  }

  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {reasons.map((reason) => (
        <li
          key={reason.code}
          className="rounded-lg border border-risk-medium/30 bg-risk-medium-bg p-3"
        >
          <p className="text-sm font-semibold text-risk-medium">{reason.label}</p>
          <p className="mt-1 text-xs leading-relaxed text-brand-navy">{reason.explanation}</p>
        </li>
      ))}
    </ul>
  );
}
