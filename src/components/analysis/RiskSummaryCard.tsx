import type { AnalysisResult } from "../../types";
import { RiskBadge } from "../common/RiskBadge";
import { VerificationStatusPill } from "../common/VerificationStatusPill";
import { modelJudgmentTermLabel } from "../../content/copy";

export function RiskSummaryCard({ analysis }: { analysis: AnalysisResult }) {
  return (
    <div className="rounded-xl border border-brand-border bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <RiskBadge level={analysis.riskLevel} />
        <VerificationStatusPill status={analysis.verificationStatus} />
      </div>

      <dl className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-brand-muted">
            風險分數
          </dt>
          <dd className="mt-1 text-lg font-semibold text-brand-navy">
            {analysis.riskScore} / 100
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-brand-muted">
            官方佐證
          </dt>
          <dd className="mt-1 text-lg font-semibold text-brand-navy">
            {analysis.hasOfficialSupport ? "已有對應公告" : "暫無對應公告"}
          </dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-xs font-medium uppercase tracking-wide text-brand-muted">
            {modelJudgmentTermLabel}
          </dt>
          <dd className="mt-1 text-lg font-semibold text-brand-navy">
            {analysis.modelJudgmentSummary}
          </dd>
        </div>
      </dl>

      <p className="mt-4 rounded-lg bg-brand-surface p-4 text-sm leading-relaxed text-brand-navy">
        {analysis.riskExplanationParagraph}
      </p>
    </div>
  );
}
