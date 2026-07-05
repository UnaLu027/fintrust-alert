import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAnalyzeSubmit } from "../../hooks/useVerify";
import { AnalysisTypeSelector } from "./AnalysisTypeSelector";
import { sourceLabels } from "../../content/copy";
import type { AnalysisType, SourceType } from "../../types";

const allSources: SourceType[] = ["x", "yahoo", "mops"];

export function VerifyForm() {
  const navigate = useNavigate();
  const analyze = useAnalyzeSubmit();

  const [keyword, setKeyword] = useState("");
  const [company, setCompany] = useState("");
  const [ticker, setTicker] = useState("");
  const [yahooUrl, setYahooUrl] = useState("");
  const [xUrl, setXUrl] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sources, setSources] = useState<SourceType[]>(allSources);
  const [analysisType, setAnalysisType] = useState<AnalysisType>("full_analysis");
  const [error, setError] = useState<string | null>(null);

  function toggleSource(source: SourceType) {
    setSources((prev) =>
      prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source],
    );
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!keyword && !company && !ticker && !yahooUrl && !xUrl) {
      setError("請至少輸入一項查證條件（關鍵字、公司、股票代號或網址）");
      return;
    }
    try {
      const res = await analyze.mutateAsync({
        keyword: keyword || undefined,
        company: company || undefined,
        ticker: ticker || undefined,
        yahooUrl: yahooUrl || undefined,
        xUrl: xUrl || undefined,
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
        sources,
        analysisTypes: [analysisType],
      });
      navigate(`/analysis/${res.analysisId}`);
    } catch {
      setError("分析請求失敗，請稍後再試");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-brand-navy">關鍵字搜尋</label>
          <input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="例如：AI、半導體、暴跌、明牌群組"
            className="mt-1 w-full rounded-md border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand-blue"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-brand-navy">公司名稱</label>
          <input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="例如：台積電、鴻海、聯發科"
            className="mt-1 w-full rounded-md border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand-blue"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-brand-navy">股票代號</label>
          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="例如：2330、2317、2454"
            className="mt-1 w-full rounded-md border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand-blue"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-brand-navy">Yahoo 財經新聞網址</label>
          <input
            value={yahooUrl}
            onChange={(e) => setYahooUrl(e.target.value)}
            placeholder="https://tw.stock.yahoo.com/news/..."
            className="mt-1 w-full rounded-md border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand-blue"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-brand-navy">X 貼文網址</label>
          <input
            value={xUrl}
            onChange={(e) => setXUrl(e.target.value)}
            placeholder="https://x.com/.../status/..."
            className="mt-1 w-full rounded-md border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand-blue"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-brand-navy">日期區間</label>
          <div className="mt-1 flex items-center gap-2">
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full rounded-md border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand-blue"
            />
            <span className="text-brand-muted">至</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full rounded-md border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand-blue"
            />
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-brand-navy">資料來源</label>
        <div className="mt-2 flex flex-wrap gap-3">
          {allSources.map((s) => (
            <label
              key={s}
              className={`cursor-pointer rounded-md border px-3 py-2 text-sm ${
                sources.includes(s)
                  ? "border-brand-blue bg-brand-sky text-brand-blue"
                  : "border-brand-border text-brand-muted"
              }`}
            >
              <input
                type="checkbox"
                className="sr-only"
                checked={sources.includes(s)}
                onChange={() => toggleSource(s)}
              />
              {sourceLabels[s]}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-brand-navy">分析類型</label>
        <div className="mt-2">
          <AnalysisTypeSelector value={analysisType} onChange={setAnalysisType} />
        </div>
      </div>

      {error && <p className="text-sm text-risk-high">{error}</p>}

      <button
        type="submit"
        disabled={analyze.isPending}
        className="w-full rounded-md bg-brand-blue py-2.5 text-sm font-semibold text-white hover:bg-brand-navy disabled:opacity-60 sm:w-auto sm:px-8"
      >
        {analyze.isPending ? "分析中..." : "開始查證"}
      </button>
    </form>
  );
}
