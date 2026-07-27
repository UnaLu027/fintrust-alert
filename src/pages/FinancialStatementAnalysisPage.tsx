import { useState } from "react";
import { useFinancialStatementAnalysis } from "../hooks/useFinancialStatementAnalysis";
import { useHistoricalFinancialAnalysis } from "../hooks/useHistoricalFinancialAnalysis";
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

function ErrorPanel({ error, source }: { error: unknown; source: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      {error instanceof Error ? error.message : `無法取得${source}分析結果`}
      <p className="mt-2 text-xs">
        本機開發請確認 FastAPI 已在 8000 port 啟動；部署環境請設定
        VITE_FINANCIAL_API_BASE_URL。MOPS 也可能暫時限制雲端 IP 或請求頻率。
      </p>
    </div>
  );
}

export function FinancialStatementAnalysisPage() {
  const [ticker, setTicker] = useState("2330");
  const [historyYears, setHistoryYears] = useState(5);
  const latestAnalysis = useFinancialStatementAnalysis(ticker);
  const historyAnalysis = useHistoricalFinancialAnalysis(ticker, historyYears);
  const latestReport = latestAnalysis.data;
  const historyReport = historyAnalysis.data;
  const historyPeriods = historyReport?.periods.filter((period) => period.status === "available") ?? [];

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm font-medium text-brand-blue">半導體產業專用</p>
        <h1 className="mt-1 text-2xl font-bold text-brand-navy">財報分析規則引擎</h1>
        <p className="mt-2 max-w-4xl text-sm leading-relaxed text-brand-muted">
          系統自動抓取 TWSE 最新公開資料與 MOPS Inline XBRL 年度財報，先以固定公式重新計算，再由版本化規則產生可追溯的趨勢與風險提示。
        </p>
      </header>

      <section className="rounded-xl border border-brand-border bg-white p-5 shadow-sm">
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

        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border border-brand-border p-4">
            <p className="text-sm font-semibold text-brand-navy">最新官方快照</p>
            <p className="mt-1 text-xs leading-relaxed text-brand-muted">
              抓取 TWSE 綜合損益表、資產負債表與月營收，適合檢查最新指標與資料一致性。
            </p>
            <button
              type="button"
              onClick={() => latestAnalysis.refetch()}
              disabled={latestAnalysis.isFetching}
              className="mt-4 rounded-md bg-brand-blue px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-navy disabled:opacity-60"
            >
              {latestAnalysis.isFetching ? "抓取並分析中..." : "分析 TWSE 最新資料"}
            </button>
          </div>

          <div className="rounded-lg border border-brand-border p-4">
            <p className="text-sm font-semibold text-brand-navy">近 3–5 年歷史財報</p>
            <p className="mt-1 text-xs leading-relaxed text-brand-muted">
              自動下載 MOPS 第 4 季／年度合併 iXBRL，分析公司自身跨期趨勢；第一版不把累計季資料誤當單季。
            </p>
            <div className="mt-4 flex flex-wrap items-end gap-3">
              <label>
                <span className="block text-xs text-brand-muted">歷史年數</span>
                <select
                  value={historyYears}
                  onChange={(event) => setHistoryYears(Number(event.target.value))}
                  className="mt-1 rounded-md border border-brand-border bg-white px-3 py-2 text-sm outline-none focus:border-brand-blue"
                >
                  <option value={3}>3 年</option>
                  <option value={4}>4 年</option>
                  <option value={5}>5 年</option>
                </select>
              </label>
              <button
                type="button"
                onClick={() => historyAnalysis.refetch()}
                disabled={historyAnalysis.isFetching}
                className="rounded-md bg-brand-blue px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-navy disabled:opacity-60"
              >
                {historyAnalysis.isFetching
                  ? "下載 MOPS iXBRL 並分析中..."
                  : "分析 MOPS 歷史財報"}
              </button>
            </div>
          </div>
        </div>
      </section>

      {latestAnalysis.isError && <ErrorPanel error={latestAnalysis.error} source=" TWSE 最新資料" />}
      {historyAnalysis.isError && <ErrorPanel error={historyAnalysis.error} source=" MOPS 歷史財報" />}

      {latestReport && (
        <section className="space-y-5">
          <div className="rounded-xl border border-brand-border bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-brand-blue">
                  TWSE 最新快照・{latestReport.industry}・{latestReport.subindustry}
                </p>
                <h2 className="mt-1 text-xl font-bold text-brand-navy">
                  {latestReport.company_name} {latestReport.ticker}
                </h2>
                <p className="mt-1 text-xs text-brand-muted">
                  財報期間：{latestReport.report_period ?? "未辨識"}・月營收期間：
                  {latestReport.monthly_revenue_period ?? "未取得"}
                </p>
              </div>
              <span
                className={`rounded-full border px-3 py-1.5 text-sm font-semibold ${severityClasses[latestReport.overall_severity]}`}
              >
                {severityLabels[latestReport.overall_severity]}
              </span>
            </div>
            <p className="mt-4 rounded-lg bg-brand-sky/40 p-4 text-sm leading-relaxed text-brand-navy">
              {latestReport.summary}
            </p>
            <div className="mt-3 text-xs text-brand-muted">
              規則版本：{latestReport.rule_version}・門檻基礎：{latestReport.threshold_basis}
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-brand-navy">最新資料重新計算指標</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {latestReport.metrics.map((metric) => (
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
          </div>

          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-brand-navy">最新快照規則結果</h2>
            <div className="space-y-3">
              {latestReport.rule_results.map((result) => (
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
          </div>
        </section>
      )}

      {historyReport && (
        <section className="space-y-5">
          <div className="rounded-xl border border-brand-border bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-brand-blue">
                  MOPS Inline XBRL・公司自身歷史基準
                </p>
                <h2 className="mt-1 text-xl font-bold text-brand-navy">
                  {historyReport.company_name} {historyReport.ticker}・{historyReport.subindustry}
                </h2>
                <p className="mt-1 text-xs text-brand-muted">
                  要求 {historyReport.requested_years} 年・成功取得 {historyReport.available_years} 年・
                  {historyReport.start_year ?? "—"} 至 {historyReport.end_year ?? "—"}
                </p>
              </div>
              <span
                className={`rounded-full border px-3 py-1.5 text-sm font-semibold ${severityClasses[historyReport.overall_severity]}`}
              >
                {severityLabels[historyReport.overall_severity]}
              </span>
            </div>
            <p className="mt-4 rounded-lg bg-brand-sky/40 p-4 text-sm leading-relaxed text-brand-navy">
              {historyReport.summary}
            </p>
            <div className="mt-3 text-xs text-brand-muted">
              規則版本：{historyReport.rule_version}・門檻基礎：{historyReport.threshold_basis}
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-brand-navy">3–5 年趨勢指標</h2>
            <div className="overflow-x-auto rounded-xl border border-brand-border bg-white shadow-sm">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs text-brand-muted">
                  <tr>
                    <th className="px-4 py-3">指標</th>
                    {historyPeriods.map((period) => (
                      <th key={period.period} className="whitespace-nowrap px-4 py-3">
                        {period.period}
                      </th>
                    ))}
                    <th className="px-4 py-3">最新變化</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border">
                  {historyReport.trend_metrics.map((metric) => (
                    <tr key={metric.code}>
                      <td className="px-4 py-3">
                        <p className="font-medium text-brand-navy">{metric.label}</p>
                        <p className="mt-1 text-xs text-brand-muted">{metric.formula}</p>
                      </td>
                      {historyPeriods.map((period) => {
                        const value = metric.period_values[period.period];
                        return (
                          <td key={period.period} className="whitespace-nowrap px-4 py-3 text-brand-navy">
                            {value === undefined ? "—" : formatValue(value, metric.unit)}
                          </td>
                        );
                      })}
                      <td className="whitespace-nowrap px-4 py-3 text-brand-muted">
                        {metric.change_percentage_points !== undefined
                          ? `${metric.change_percentage_points >= 0 ? "+" : ""}${metric.change_percentage_points.toFixed(2)} 個百分點`
                          : metric.change_percent !== undefined
                            ? `${metric.change_percent >= 0 ? "+" : ""}${metric.change_percent.toFixed(2)}%`
                            : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-brand-navy">歷史複合規則結果</h2>
            <div className="space-y-3">
              {historyReport.rule_results.map((result) => (
                <article key={result.rule_id} className="rounded-xl border border-brand-border bg-white p-4 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs text-brand-muted">
                        {result.rule_id}・{result.category}・{result.evidence_periods.join("、") || "期間不足"}
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
          </div>

          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-brand-navy">MOPS 年度資料涵蓋</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {historyReport.periods.map((period) => (
                <article key={period.period} className="rounded-xl border border-brand-border bg-white p-4 shadow-sm">
                  <p className="text-xs text-brand-muted">
                    {period.status === "available" ? "已取得" : period.status === "missing" ? "欄位不足" : "下載／解析失敗"}
                  </p>
                  <h3 className="mt-1 text-sm font-semibold text-brand-navy">{period.period} 合併財報</h3>
                  <p className="mt-2 text-xs text-brand-muted">
                    已映射 {period.fields_found.length} 欄；缺少 {period.fields_missing.length} 欄
                  </p>
                  {period.warnings.length > 0 && (
                    <p className="mt-2 text-xs leading-relaxed text-amber-800">{period.warnings.join("；")}</p>
                  )}
                  <a
                    href={period.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-3 inline-block text-xs font-medium text-brand-blue hover:underline"
                  >
                    查看／下載官方 iXBRL
                  </a>
                </article>
              ))}
            </div>
          </div>

          <section className="rounded-xl border border-amber-200 bg-amber-50 p-5">
            <h2 className="font-semibold text-amber-900">歷史資料與方法限制</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs leading-relaxed text-amber-900">
              {historyReport.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </section>
        </section>
      )}

      {!latestReport && !historyReport && !latestAnalysis.isFetching && !historyAnalysis.isFetching && (
        <div className="rounded-xl border border-dashed border-brand-border bg-white p-10 text-center text-sm text-brand-muted">
          選擇公司後，可分別執行最新快照分析或 MOPS 近 3–5 年歷史分析。系統不需要使用者手動上傳財報。
        </div>
      )}
    </div>
  );
}
