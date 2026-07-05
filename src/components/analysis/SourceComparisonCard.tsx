import type { SourceComparison } from "../../types";
import { SourceTag } from "../common/SourceTag";
import { sourceComparisonIntro } from "../../content/copy";

const relationLabels = {
  supports: "支持",
  inconsistent: "不一致",
  partially_related: "僅部分相關",
};

const statusTagLabels = {
  official_confirmed: "官方已確認",
  supportable: "可佐證",
  no_official_support: "暫無官方佐證／待查證",
  pending: "待查證",
};

const statusTagStyles = {
  official_confirmed: "bg-risk-low-bg text-risk-low",
  supportable: "bg-risk-low-bg text-risk-low",
  no_official_support: "bg-risk-high-bg text-risk-high",
  pending: "bg-brand-sky text-brand-blue",
};

function formatTime(iso?: string) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function SourceComparisonCard({ comparison }: { comparison: SourceComparison }) {
  const introText =
    comparison.source === "mops"
      ? undefined
      : sourceComparisonIntro[comparison.source];

  return (
    <div className="flex h-full flex-col rounded-xl border border-brand-border bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <SourceTag source={comparison.source} />
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${statusTagStyles[comparison.statusTag]}`}
        >
          {statusTagLabels[comparison.statusTag]}
        </span>
      </div>

      <div className="mt-3 flex-1 space-y-2">
        {comparison.source === "x" && (
          <>
            <p className="text-sm leading-relaxed text-brand-navy">{comparison.summary}</p>
            <p className="text-xs text-brand-muted">
              {comparison.handleOrOutlet} ・ {formatTime(comparison.publishedAt)}
            </p>
          </>
        )}

        {comparison.source === "yahoo" && comparison.hasContent && (
          <>
            <p className="text-sm font-medium leading-relaxed text-brand-navy">
              {comparison.title}
            </p>
            <p className="text-xs text-brand-muted">
              {comparison.handleOrOutlet} ・ {formatTime(comparison.publishedAt)}
            </p>
            {comparison.relationToOriginal && (
              <p className="text-xs text-brand-muted">
                與原資訊關係：
                <span className="font-medium text-brand-navy">
                  {relationLabels[comparison.relationToOriginal]}
                </span>
              </p>
            )}
          </>
        )}

        {comparison.source === "mops" && comparison.hasContent && (
          <>
            <p className="text-sm font-medium leading-relaxed text-brand-navy">
              {comparison.title}
            </p>
            <p className="text-xs text-brand-muted">{formatTime(comparison.publishedAt)}</p>
          </>
        )}

        <p className="text-sm leading-relaxed text-brand-navy">{comparison.modelJudgment}</p>

        {comparison.riskTags && comparison.riskTags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {comparison.riskTags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-risk-high-bg px-2 py-0.5 text-[11px] font-medium text-risk-high"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {introText && (
        <p className="mt-3 border-t border-brand-border pt-3 text-xs leading-relaxed text-brand-muted">
          {introText}
        </p>
      )}
    </div>
  );
}
