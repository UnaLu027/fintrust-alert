import { useState } from "react";
import { usePersistedFinancialAnalysis } from "../hooks/usePersistedFinancialAnalysis";
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

function formatValue(value: number | undefined, unit: string) {
  if (value === undefined || value === null) return "—";
  const maximumFractionDigits = Math.abs(value) >= 1000 ? 0 : 2;
  const number = new Intl.NumberFormat("zh-TW", { maximumFractionDigits }).format(value);
  return unit === "%" || unit === "百分點" ? `${number}${unit}` : `${number} ${unit}`;
}

export function FinancialStatementAnalysisPage() {
  const [ticker, setTicker] = useState("2330");
  const analysis = usePersistedFinancialAnalysis(ticker);
  const snapshot = analysis.data;

  return (
    <div className="space-y-7">
      <header>
        <p className="text-sm font-medium text-brand-blue">半導體產業專用</p>
        <h1 className="mt-1 text-2xl font-bold text-brand-navy">財報分析規則引擎</h1>
        <p className="mt-2 max-w-4xl text-sm leading-relaxed text-brand-muted">
          後端排程會自動抓取 TWSE 與 MOPS Inline XBRL、寫入資料庫、計算指標並執行子產業規則；本頁只讀取最新完成的分析快照。
        </p>
      </header>

      <section className="rounded-xl border border-brand-border bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-end gap-3">
          <label className="min-w-72 flex-1">
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
            className="rounded-md border border-brand-blue px-4 py-2 text-sm font-semibold text-brand-blue disabled:opacity-60"
          >
            {analysis.isFetching ? "同步中..." : "重新讀取最新快照"}
          </button>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-brand-muted">
          此按鈕只重新讀取資料庫，不會在使用者頁面即時下載五年財報；資料更新由 Cloud Scheduler 或管理端 refresh pipeline 執行。
        </p>
      </section>

      {analysis.isLoading && (
        <div className="rounded-xl border border-brand-border bg-white p-6 text-sm text-brand-muted">
          正在讀取最新分析快照…
        </div>
      )}

      {analysis.isError && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">
          {analysis.error instanceof Error ? analysis.error.message : "無法讀取財報分析快照"}
        </div>
      )}

      {!analysis.isLoading && !analysis.isError && snapshot === null && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm leading-relaxed text-amber-900">
          此公司尚無完成的分析快照。部署後由每日排程自動建立；Demo 可在 FastAPI /docs 由管理端觸發 refresh。
        </div>
      )}

      {snapshot && (
        <>
          <section className="rounded-xl border border-brand-border bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-brand-blue">
                  最新持久化分析・{snapshot.subindustry}
                </p>
                <h2 className="mt-1 text-xl font-bold text-brand-navy">
                  {snapshot.company_name} {snapshot.ticker}
                </h2>
                <p className="mt-1 text-xs text-brand-muted">
                  更新時間：{new Date(snapshot.data_updated_at).toLocaleString("zh-TW")}・Run ID：
                  {snapshot.analysis_run_id.slice(0, 12)}
                </p>
              </div>
              <span
                className={`rounded-full border px-3 py-1.5 text-sm font-semibold ${severityClasses[snapshot.overall_severity]}`}
              >
                {severityLabels[snapshot.overall_severity]}
              </span>
            </div>
            <p className="mt-4 rounded-lg bg-brand-sky/40 p-4 text-sm leading-relaxed text-brand-navy">
              {snapshot.summary}
            </p>
            <p className="mt-3 text-xs text-brand-muted">
              規則版本：{snapshot.rule_version}・門檻基礎：{snapshot.threshold_basis}
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-brand-navy">子產業關鍵指標</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {snapshot.key_metrics.map((metric) => (
                <article key={metric.code} className="rounded-xl border border-brand-border bg-white p-4 shadow-sm">
                  <p className="text-xs text-brand-muted">{metric.category}</p>
                  <h3 className="mt-1 text-sm font-semibold text-brand-navy">{metric.label}</h3>
                  <p className="mt-3 text-2xl font-bold text-brand-blue">
                    {formatValue(metric.latest_value, metric.unit)}
                  </p>
                  <p className="mt-3 rounded bg-slate-50 px-2 py-1.5 text-xs leading-relaxed text-brand-muted">
                    {metric.formula}
                  </p>
                </article>
              ))}
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold text-brand-navy">可解釋規則結果</h2>
            <div className="space-y-3">
              {snapshot.rule_cards.map((rule) => (
                <article key={`${rule.rule_scope}-${rule.rule_id}`} className="rounded-xl border border-brand-border bg-white p-4 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs text-brand-muted">
                        {rule.rule_id}・{rule.category}・{rule.rule_scope}
                      </p>
                      <h3 className="mt-1 font-semibold text-brand-navy">{rule.name}</h3>
                    </div>
                    <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${severityClasses[rule.severity]}`}>
                      {severityLabels[rule.severity]}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-brand-muted">{rule.explanation}</p>
                  <p className="mt-2 text-xs text-brand-muted">門檻：{rule.threshold_description}</p>
                  {rule.logic_expression && (
                    <p className="mt-2 rounded bg-slate-50 px-2 py-1.5 font-mono text-xs text-brand-muted">
                      {rule.logic_expression}
                    </p>
                  )}
                </article>
              ))}
            </div>
          </section>

          <section className="rounded-xl border border-brand-border bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-brand-navy">官方資料來源</h2>
            <div className="mt-3 space-y-2 text-sm">
              {snapshot.sources.map((source) => (
                <a
                  key={`${source.source_url}-${source.period ?? "latest"}`}
                  href={source.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="block text-brand-blue hover:underline"
                >
                  {source.source_name}・{source.period ?? "最新快照"}・{source.status}
                </a>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
