import type {
  FinancialEvidenceResult,
  FinancialVerificationVerdict,
  OfficialFinancialEvidence,
} from "../../types";

const verdictLabels: Record<FinancialVerificationVerdict, string> = {
  supported: "財報支持",
  partially_supported: "部分支持",
  contradicted: "與財報不符",
  insufficient_evidence: "證據不足",
  not_applicable: "不適用財報查證",
};

const verdictClasses: Record<FinancialVerificationVerdict, string> = {
  supported: "border-emerald-200 bg-emerald-50 text-emerald-800",
  partially_supported: "border-amber-200 bg-amber-50 text-amber-800",
  contradicted: "border-red-200 bg-red-50 text-red-800",
  insufficient_evidence: "border-slate-200 bg-slate-50 text-slate-700",
  not_applicable: "border-slate-200 bg-white text-slate-600",
};

function formatNumber(value: number | undefined, unit: string) {
  if (value === undefined) return "—";
  const formatted = new Intl.NumberFormat("zh-TW", {
    maximumFractionDigits: 2,
  }).format(value);
  return `${formatted}${unit === "%" || unit === "百分點" ? unit : ` ${unit}`}`;
}

function EvidenceDetails({ evidence }: { evidence: OfficialFinancialEvidence }) {
  return (
    <div className="rounded-lg border border-brand-border bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-brand-navy">
            {evidence.metric}・{evidence.period}
          </p>
          <p className="mt-1 text-xs text-brand-muted">
            {evidence.sourceName}・{evidence.dataCoverage}
          </p>
        </div>
        {evidence.isDemo && (
          <span className="rounded-full border border-amber-300 bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">
            Demo fixture
          </span>
        )}
      </div>

      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <dt className="text-xs text-brand-muted">本期官方值</dt>
          <dd className="mt-1 font-medium text-brand-navy">
            {formatNumber(evidence.currentValue, evidence.unit)}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-brand-muted">比較期官方值</dt>
          <dd className="mt-1 font-medium text-brand-navy">
            {formatNumber(evidence.comparisonValue, evidence.unit)}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-brand-muted">重新計算結果</dt>
          <dd className="mt-1 font-medium text-brand-navy">
            {formatNumber(evidence.calculatedValue, "%")}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-brand-muted">容許誤差</dt>
          <dd className="mt-1 font-medium text-brand-navy">
            {evidence.tolerance === undefined ? "—" : `±${evidence.tolerance} 個百分點`}
          </dd>
        </div>
      </dl>

      {evidence.formula && (
        <div className="mt-4 rounded-md bg-white px-3 py-2 font-mono text-xs text-brand-navy">
          {evidence.formula}
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-brand-muted">
        <span>資料更新：{new Date(evidence.lastUpdatedAt).toLocaleString("zh-TW")}</span>
        <a
          href={evidence.sourceUrl}
          target="_blank"
          rel="noreferrer"
          className="font-medium text-brand-blue hover:underline"
        >
          查看官方來源
        </a>
      </div>
    </div>
  );
}

export function FinancialEvidencePanel({ result }: { result: FinancialEvidenceResult }) {
  const evidenceById = new Map(result.evidence.map((item) => [item.id, item]));

  return (
    <section className="space-y-4 rounded-xl border border-brand-border bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-brand-blue">
            半導體產業・官方量化證據層
          </p>
          <h2 className="mt-1 text-lg font-semibold text-brand-navy">官方財報證據</h2>
          <p className="mt-1 max-w-3xl text-sm leading-relaxed text-brand-muted">
            AI 僅負責抽取主張與對齊證據；數值、公式與最終量化比對由確定性程式重新計算。
          </p>
        </div>
        <span
          className={`rounded-full border px-3 py-1 text-sm font-semibold ${verdictClasses[result.overallVerdict]}`}
        >
          {verdictLabels[result.overallVerdict]}
        </span>
      </div>

      <div className="rounded-lg border border-brand-border bg-brand-sky/40 p-4 text-sm leading-relaxed text-brand-navy">
        {result.summary}
      </div>

      <div className="space-y-4">
        {result.claims.map((item, index) => {
          const linkedEvidence = item.evidenceIds
            .map((id) => evidenceById.get(id))
            .filter((evidence): evidence is OfficialFinancialEvidence => Boolean(evidence));

          return (
            <article key={item.claim.id} className="rounded-xl border border-brand-border p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs text-brand-muted">財務主張 {index + 1}</p>
                  <blockquote className="mt-1 border-l-4 border-brand-blue pl-3 text-sm font-medium leading-relaxed text-brand-navy">
                    {item.claim.originalText}
                  </blockquote>
                </div>
                <span
                  className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${verdictClasses[item.verdict]}`}
                >
                  {verdictLabels[item.verdict]}
                </span>
              </div>

              <dl className="mt-4 grid gap-3 rounded-lg bg-slate-50 p-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <dt className="text-xs text-brand-muted">公司／代號</dt>
                  <dd className="mt-1 font-medium text-brand-navy">
                    {item.claim.companyName ?? "未辨識"}
                    {item.claim.ticker ? ` ${item.claim.ticker}` : ""}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-brand-muted">半導體子產業</dt>
                  <dd className="mt-1 font-medium text-brand-navy">
                    {item.claim.semiconductorSubindustry ?? "待分類"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-brand-muted">指標與期間</dt>
                  <dd className="mt-1 font-medium text-brand-navy">
                    {item.claim.metric ?? "未辨識"}・{item.claim.period ?? "期間不明"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-brand-muted">主張幅度</dt>
                  <dd className="mt-1 font-medium text-brand-navy">
                    {item.claim.claimedChangePercent === undefined
                      ? "未抽取"
                      : `${item.claim.claimedChangePercent}%`}
                  </dd>
                </div>
              </dl>

              <p className="mt-3 text-sm leading-relaxed text-brand-muted">{item.explanation}</p>

              {linkedEvidence.length > 0 && (
                <div className="mt-4 space-y-3">
                  {linkedEvidence.map((evidence) => (
                    <EvidenceDetails key={evidence.id} evidence={evidence} />
                  ))}
                </div>
              )}
            </article>
          );
        })}
      </div>

      {result.limitations.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
          <h3 className="text-sm font-semibold text-amber-900">資料與方法限制</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-xs leading-relaxed text-amber-900">
            {result.limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
