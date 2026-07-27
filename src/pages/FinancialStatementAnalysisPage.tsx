import { useState } from "react";
import { useFinancialStatementAnalysis } from "../hooks/useFinancialStatementAnalysis";
import type { RuleSeverity } from "../types";

const companies = [
  { ticker: "2330", name: "台積電", subindustry: "晶圓代工" },
  { ticker: "2303", name: "聯電", subindustry: "晶圓代工" },
  { ticker: "2454", name: "聯發科", subindustry: "IC 設計" },
  { ticker: "3711", name: "日月光投控", subindustry: "封裝測試" },
];

const severityLabels: Record<RuleSeverity, string> = {
  positive: "正向觀察",
  normal: "未觸發",
  attention: "需注意",
  high_attention: "高關注",
  data_issue: "資料問題",
  insufficient_data: "資料不足",
};

const severityClasses: Record<RuleSeverity, string> = {
  positive: "border-emerald-200 bg-emerald-50 text-emerald-800",
  normal: "border-slate-200 bg-slate-50 text-slate-700",
  attention: "border-amber-200 bg-amber-50 text-amber-900",
  high_attention: "border-red-200 bg-red-50 text-red-800",
  data_issue: "border-fuchsia-200 bg-fuchsia-50 text-fuchsia-800",
  insufficient_data: "border-slate-200 bg-white text-slate-500",
};

function formatValue(value: number, unit: string) {
  const maximumFractionDigits = Math.abs(value) >= 1000 ? 0 : 2;
  const number = new Intl.NumberFormat("zh-TW", { maximumFractionDigits }).format(value);
  return unit === "%" || unit === "百分點" ? `${number}${unit}` : `${number} ${unit}`;
}

export function FinancialStatementAnalysisPage() {
  const [ticker, setTicker] = useState("2330");
  const analysis = useFinancialStatementAnalysis(ticker);
  const report = analysis.data;

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-brand-blue">半導體產業專用</p>
        <h1 className="mt-1 text-2xl font-bold text-brand-navy">財報分析規則引擎</h1>
        <p className="mt-2 max-w-4xl text-sm leading-relaxed text-brand-muted">
          系統直接抓取臺灣證券交易所公開的綜合損益表、資產負債表與月營收，先以固定公式計算財務指標，再由版本化規則產生可追溯的分析結果。
        </p>
      </header>

      <section className="rounded-xl border border-brand-border bg-white p-5 shadow-sm">
        <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-end">
          <label className="block">
            <span className="text-sm font-medium text-brand-navy">選擇半導體公司</span>
            <select
              value={ticker}
              onChange={(event) => setTicker(event.target.value)}
              className="mt-1 w-full rounded-md border border-brand-border bg-white px-3 py-2 text-sm outline-none focus:border-brand-blue"
            >
              {companies.map((company) => (
                <option key={company.ticker} value={company.ticker}>
                  {company.name} {company.ticker}・{company.subindustry}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => analysis.refetch()}
            disabled={analysis.isFetching}
            className="rounded-md bg-brand-blue px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-navy disabled:opacity-60"
          >
            {analysis.isFetching ? "抓取並分析中..." : "抓取官方財報並分析"}
          </button>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-brand-muted">
          目前採用 TWSE 最新公開快照；近 3–5 年趨勢與現金流規則將在 MOPS Inline XBRL 歷史資料接入後啟用。
        </p>
      </section>

      {analysis.isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {analysis.error instanceof Error ? analysis.error.message : "無法取得分析結果"}
          <p className="mt-2 text-xs">
            本機開發請確認 FastAPI 已在 8000 port 啟動；部署環境請設定 VITE_FINANCIAL_API_BASE_URL。
          </p>
        </div>
      )}

      {!report && !analysis.isFetching && !analysis.isError && (
        <div className="rounded-xl border border-dashed border-brand-border bg-white p-10 text-center text-sm text-brand-muted">
          選擇公司後按下「抓取官方財報並分析」，系統才會向官方資料來源提出請求。
        </div>
      )}

      {report && (
        <>
          <section className="rounded-xl border border-brand-border bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-brand-blue">
                  {report.industry}・{report.subindustry}
                </p>
                <h2 className="mt-1 text-xl font-bold text-brand-navy">
                  {report.company_name} {report.ticker}
                </h2>
                <p className="mt-1 text-xs text-brand-muted">
                  財報期間：{report.report_period ?? "未辨識"}・月營收期間：
                  {report.monthly_revenue_period ?? "未取得"}
                </p>
              </div>
              <span
                className={`rounded-full border px-3 py-1.5 text-sm font-semibold ${severityClasses[report.overall_severity]}`}
              >
                {severityLabels[report.overall_severity]}
              </span>
            </div>
            <p className="mt-4 rounded-lg bg-brand-sky/40 p-4 text-sm leading-relaxed text-brand-navy">
              {report.summary}
            </p>
            <div className="mt-3 text-xs text-brand-muted">
              規則版本：{report.rule_version}・門檻基礎：{report.threshold_basis}
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-brand-navy">系統重新計算的財務指標</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {report.metrics.map((metric) => (
                <article key={metric.code} className="rounded-xl border border-brand-border bg-white p-4 shadow-sm">
                  <p className="text-xs text-brand-muted">{metric.category}</p>
                  <h3 className="mt-1 text-sm font-semibold text-brand-navy">{metric.label}</h3>
                  <p className="mt-3 text-2xl font-bold text-brand-blue">
                    {formatValue(metric.value, metric.unit)}
                  </p>
                  <p className="mt-3 rounded bg-slate-50 px-2 py-1.5 text-xs leading-relaxed text-brand-muted">
                    {metric.formula}
                  </p>
                </article>
              ))}
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-brand-navy">規則判斷結果</h2>
            <div className="space-y-3">
              {report.rule_results.map((result) => (
                <article key={result.rule_id} className="rounded-xl border border-brand-border bg-white p-4 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs text-brand-muted">
                        {result.rule_id}・{result.category}
                      </p>
                      <h3 className="mt-1 font-semibold text-brand-navy">{result.name}</h3>
                    </div>
                    <span
                      className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${severityClasses[result.severity]}`}
                    >
                      {severityLabels[result.severity]}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-brand-muted">{result.explanation}</p>
                  <p className="mt-2 text-xs text-brand-muted">門檻：{result.threshold_description}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-brand-navy">官方資料來源與涵蓋範圍</h2>
            <div className="grid gap-4 md:grid-cols-3">
              {report.statement.source_coverage.map((source) => (
                <article key={source.source_url} className="rounded-xl border border-brand-border bg-white p-4 shadow-sm">
                  <p className="text-xs text-brand-muted">{source.status === "available" ? "已取得" : "未取得"}</p>
                  <h3 className="mt-1 text-sm font-semibold text-brand-navy">{source.source_name}</h3>
                  <p className="mt-2 text-xs text-brand-muted">期間：{source.report_period ?? "未辨識"}</p>
                  <p className="mt-1 text-xs text-brand-muted">
                    已取得 {source.fields_found.length} 欄；缺少 {source.fields_missing.length} 欄
                  </p>
                  <a
                    href={source.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-3 inline-block text-xs font-medium text-brand-blue hover:underline"
                  >
                    查看官方 API
                  </a>
                </article>
              ))}
            </div>
          </section>

          <section className="rounded-xl border border-amber-200 bg-amber-50 p-5">
            <h2 className="font-semibold text-amber-900">方法與資料限制</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs leading-relaxed text-amber-900">
              {report.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}
