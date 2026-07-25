import { useParams } from "react-router-dom";
import { useAnalysisResult } from "../hooks/useAnalysisResult";
import { LoadingState } from "../components/common/LoadingState";
import { EmptyState } from "../components/common/EmptyState";
import { VerificationStatusPill } from "../components/common/VerificationStatusPill";
import { SourceTag } from "../components/common/SourceTag";
import { RiskSummaryCard } from "../components/analysis/RiskSummaryCard";
import { RiskReasonList } from "../components/analysis/RiskReasonList";
import { SourceComparisonCard } from "../components/analysis/SourceComparisonCard";
import { FinancialEvidencePanel } from "../components/analysis/FinancialEvidencePanel";
import { DisclaimerBanner } from "../components/common/DisclaimerBanner";
import { fixedDisclaimer } from "../content/disclaimers";

function formatTime(iso: string) {
  return new Date(iso).toLocaleString("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function AnalysisResultPage() {
  const { id } = useParams<{ id: string }>();
  const { data: analysis, isLoading } = useAnalysisResult(id);

  if (isLoading) return <LoadingState label="正在載入分析結果..." />;
  if (!analysis) return <EmptyState label="找不到此分析結果" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <VerificationStatusPill status={analysis.classification} />
          {analysis.sources.map((s) => (
            <SourceTag key={s} source={s} />
          ))}
        </div>
        <h1 className="mt-3 text-2xl font-bold text-brand-navy">{analysis.title}</h1>
        <p className="mt-1 text-sm text-brand-muted">
          關聯標的：{analysis.relatedCompany}
          {analysis.relatedTicker ? ` ${analysis.relatedTicker}` : ""} ・ 分析時間：
          {formatTime(analysis.analyzedAt)}
        </p>
      </div>

      <RiskSummaryCard analysis={analysis} />

      {analysis.financialEvidence && (
        <FinancialEvidencePanel result={analysis.financialEvidence} />
      )}

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-brand-navy">風險原因</h2>
        <RiskReasonList reasons={analysis.riskReasons} />
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-brand-navy">多來源查證</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {analysis.sourceComparisons.map((comparison) => (
            <SourceComparisonCard key={comparison.source} comparison={comparison} />
          ))}
        </div>
      </div>

      <DisclaimerBanner text={fixedDisclaimer} />
    </div>
  );
}
