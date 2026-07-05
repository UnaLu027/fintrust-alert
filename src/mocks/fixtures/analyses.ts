import type { AnalysisResult, RiskReason, RiskReasonCode } from "../../types";
import { modelJudgmentPhrasing, riskExplanationParagraph } from "../../content/riskExplanations";
import { mopsComparisonText, riskReasonLabels, sourceComparisonIntro } from "../../content/copy";

function reason(code: RiskReasonCode): RiskReason {
  return { code, ...riskReasonLabels[code] };
}

/**
 * 4 canned demo scenarios (spec section 十五). Each one is cross-referenced
 * by id from dashboardStats.ts, pushAlerts.ts and historyRecords.ts so the
 * dashboard -> analysis result -> alerts/history flow resolves consistently.
 */
export const demoAnalyses: AnalysisResult[] = [
  // Demo 1: 社群疑似假訊息
  {
    id: "demo-tsmc-crash-rumor",
    title: "台積電即將暴跌，內線消息外流？X 貼文瘋傳",
    classification: "suspected_false",
    relatedCompany: "台積電",
    relatedTicker: "2330",
    sources: ["x", "yahoo", "mops"],
    analyzedAt: "2026-07-06T08:12:00+08:00",
    riskLevel: "high",
    riskScore: 91,
    verificationStatus: "suspected_false",
    hasOfficialSupport: false,
    modelJudgmentSummary: modelJudgmentPhrasing("high"),
    riskExplanationParagraph: riskExplanationParagraph("high"),
    riskReasons: [
      reason("exaggerated_tone"),
      reason("insufficient_official_support"),
      reason("abnormal_social_spread"),
      reason("investment_inducement_risk"),
    ],
    analysisTypesRequested: ["full_analysis"],
    sourceComparisons: [
      {
        source: "x",
        hasContent: true,
        summary:
          "「台積電內部消息，Q3 訂單被大砍，股價撐不住了，現在不出場就晚了」，貼文附加多張未具名截圖。",
        handleOrOutlet: "@trader_insider_tw",
        publishedAt: "2026-07-06T02:30:00+08:00",
        modelJudgment: "疑似誇大，且缺乏可查證的具體依據",
        riskTags: ["投資誘導", "缺乏佐證", "社群擴散"],
        disclaimerText: sourceComparisonIntro.x,
        statusTag: "no_official_support",
      },
      {
        source: "yahoo",
        hasContent: false,
        modelJudgment: "目前尚未有主流財經新聞報導相關說法",
        disclaimerText: sourceComparisonIntro.yahoo,
        statusTag: "pending",
      },
      {
        source: "mops",
        hasContent: false,
        modelJudgment: mopsComparisonText(false, "台積電").text,
        disclaimerText: "",
        statusTag: "no_official_support",
      },
    ],
  },

  // Demo 2 (flagship example from spec section 七): 新聞待查證＋誇大表述
  {
    id: "demo-q2-revenue-surge",
    title: "台積電 Q2 營收將暴增 50%？法人：目標價上看 1000 元",
    classification: "pending",
    relatedCompany: "台積電",
    relatedTicker: "2330",
    sources: ["x", "yahoo", "mops"],
    analyzedAt: "2026-07-05T22:30:00+08:00",
    riskLevel: "high",
    riskScore: 87,
    verificationStatus: "pending",
    hasOfficialSupport: false,
    modelJudgmentSummary: modelJudgmentPhrasing("high"),
    riskExplanationParagraph: riskExplanationParagraph("high"),
    riskReasons: [
      reason("exaggerated_tone"),
      reason("insufficient_official_support"),
      reason("incomplete_information"),
    ],
    analysisTypesRequested: ["full_analysis"],
    sourceComparisons: [
      {
        source: "x",
        hasContent: true,
        summary: "多則貼文轉貼同一張法人報告截圖，附加「上看千元」等字眼，來源不明。",
        handleOrOutlet: "@ai_stock_channel",
        publishedAt: "2026-07-05T21:40:00+08:00",
        modelJudgment: "疑似誇大轉載，尚未見完整報告來源",
        riskTags: ["缺乏佐證", "社群擴散"],
        disclaimerText: sourceComparisonIntro.x,
        statusTag: "no_official_support",
      },
      {
        source: "yahoo",
        hasContent: true,
        title: "台積電 Q2 營收將暴增 50%？法人：目標價上看 1000 元",
        publishedAt: "2026-07-05T22:10:00+08:00",
        handleOrOutlet: "Yahoo 財經",
        relationToOriginal: "partially_related",
        modelJudgment: "新聞引用單一法人預測，用語偏向誇大，尚待官方數字確認",
        disclaimerText: sourceComparisonIntro.yahoo,
        statusTag: "pending",
      },
      {
        source: "mops",
        hasContent: false,
        modelJudgment: mopsComparisonText(false, "台積電").text,
        disclaimerText: "",
        statusTag: "no_official_support",
      },
    ],
  },

  // Demo 3: 多來源不一致
  {
    id: "demo-multi-source-conflict",
    title: "鴻海海外新廠傳出投產延宕，法人看法分歧",
    classification: "inconsistent",
    relatedCompany: "鴻海",
    relatedTicker: "2317",
    sources: ["x", "yahoo", "mops"],
    analyzedAt: "2026-07-06T10:05:00+08:00",
    riskLevel: "medium",
    riskScore: 62,
    verificationStatus: "inconsistent",
    hasOfficialSupport: false,
    modelJudgmentSummary: modelJudgmentPhrasing("medium"),
    riskExplanationParagraph: riskExplanationParagraph("medium"),
    riskReasons: [reason("source_inconsistency"), reason("incomplete_information")],
    analysisTypesRequested: ["multi_source_verification"],
    sourceComparisons: [
      {
        source: "x",
        hasContent: true,
        summary: "有貼文稱海外新廠因缺工「確定延後量產至少一季」。",
        handleOrOutlet: "@supply_chain_watch",
        publishedAt: "2026-07-06T08:50:00+08:00",
        modelJudgment: "與 Yahoo 財經報導的說法不一致",
        riskTags: ["來源不一致"],
        disclaimerText: sourceComparisonIntro.x,
        statusTag: "pending",
      },
      {
        source: "yahoo",
        hasContent: true,
        title: "鴻海回應海外新廠傳聞：產線建置按原計畫推進",
        publishedAt: "2026-07-06T09:30:00+08:00",
        handleOrOutlet: "Yahoo 財經",
        relationToOriginal: "inconsistent",
        modelJudgment: "與社群說法相反，建議查看兩者原文",
        disclaimerText: sourceComparisonIntro.yahoo,
        statusTag: "pending",
      },
      {
        source: "mops",
        hasContent: false,
        modelJudgment: mopsComparisonText(false, "鴻海").text,
        disclaimerText: "",
        statusTag: "pending",
      },
    ],
  },

  // Demo 4: 官方佐證更新
  {
    id: "demo-mops-confirmed",
    title: "台積電公開資訊觀測站公告：Q2 法說會重大訊息，資本支出上修",
    classification: "official_confirmed",
    relatedCompany: "台積電",
    relatedTicker: "2330",
    sources: ["x", "yahoo", "mops"],
    analyzedAt: "2026-07-04T16:20:00+08:00",
    riskLevel: "low",
    riskScore: 12,
    verificationStatus: "official_confirmed",
    hasOfficialSupport: true,
    modelJudgmentSummary: modelJudgmentPhrasing("low"),
    riskExplanationParagraph: riskExplanationParagraph("low"),
    riskReasons: [],
    analysisTypesRequested: ["full_analysis"],
    sourceComparisons: [
      {
        source: "x",
        hasContent: true,
        summary: "多則貼文轉貼法說會重點整理，內容與公告一致。",
        handleOrOutlet: "@tw_finance_daily",
        publishedAt: "2026-07-04T16:40:00+08:00",
        modelJudgment: "內容與官方公告一致，未見明顯誇大用語",
        disclaimerText: sourceComparisonIntro.x,
        statusTag: "supportable",
      },
      {
        source: "yahoo",
        hasContent: true,
        title: "台積電法說會：資本支出上修，Q2 營運展望正向",
        publishedAt: "2026-07-04T16:35:00+08:00",
        handleOrOutlet: "Yahoo 財經",
        relationToOriginal: "supports",
        modelJudgment: "新聞內容與公開資訊觀測站公告相符",
        disclaimerText: sourceComparisonIntro.yahoo,
        statusTag: "supportable",
      },
      {
        source: "mops",
        hasContent: true,
        title: "本公司 115 年第2季法人說明會重大訊息公告",
        publishedAt: "2026-07-04T16:00:00+08:00",
        handleOrOutlet: "公開資訊觀測站",
        modelJudgment: mopsComparisonText(true, "台積電").text,
        disclaimerText: "",
        statusTag: "official_confirmed",
      },
    ],
  },
];

export function findAnalysisById(id: string): AnalysisResult | undefined {
  return demoAnalyses.find((a) => a.id === id);
}
