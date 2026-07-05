import type {
  AlertFrequency,
  AlertTypePref,
  AnalysisType,
  InvestmentExperience,
  PushTemplateType,
  RiskReasonCode,
  SourceType,
  VerificationStatus,
  WatchedMarket,
} from "../types";
import { pushDisclaimerSuffix } from "./disclaimers";

export const brand = {
  name: "FinTrust Alert",
  fullName: "FinTrust Alert｜金融資訊可信度風險提醒系統",
  tagline: "幫助你判斷資訊需不需要查證，而不是叫你買賣。",
};

export const verificationStatusLabels: Record<VerificationStatus, string> = {
  pending: "待查證",
  inconsistent: "多來源不一致",
  official_confirmed: "官方已確認",
  suspected_false: "疑似假訊息",
};

/** short "模型判斷" column label used in list/table views (dashboard, history) */
export const modelJudgmentShortLabel: Record<VerificationStatus, string> = {
  suspected_false: "疑似假訊息",
  pending: "待判斷",
  inconsistent: "待判斷",
  official_confirmed: "可信",
};

export const sourceLabels: Record<SourceType, string> = {
  x: "X",
  yahoo: "Yahoo 財經",
  mops: "公開資訊觀測站",
};

export const analysisTypeLabels: Record<AnalysisType, string> = {
  authenticity_check: "真偽輔助判斷",
  exaggeration_detection: "誇大表述偵測",
  investment_inducement_risk: "投資誘導風險",
  multi_source_verification: "多來源查證",
  full_analysis: "全部分析",
};

export const analysisTypeDescriptions: Record<AnalysisType, string> = {
  authenticity_check: "判斷內容是否疑似假訊息或可信度偏低",
  exaggeration_detection: "偵測暴漲、必漲、穩賺、上看等高強度投資語句",
  investment_inducement_risk: "偵測加入群組、明牌、保證獲利等語句",
  multi_source_verification: "比對 X、Yahoo 財經與公開資訊觀測站是否一致",
  full_analysis: "綜合以上四項進行完整分析",
};

export const riskReasonLabels: Record<
  RiskReasonCode,
  { label: string; explanation: string }
> = {
  exaggerated_tone: {
    label: "誇大語氣",
    explanation:
      "內容出現「暴增」「上看」「現在不上車就晚了」等高強度投資用語，可能造成過度解讀。",
  },
  insufficient_official_support: {
    label: "官方佐證不足",
    explanation: "目前尚未找到可直接支持此說法的官方公告。",
  },
  source_inconsistency: {
    label: "來源不一致",
    explanation: "不同來源間存在資訊落差，建議查看各來源原文。",
  },
  abnormal_social_spread: {
    label: "社群擴散異常",
    explanation: "X 上出現多則高度相似內容，可能存在重複擴散風險。",
  },
  investment_inducement_risk: {
    label: "投資誘導風險",
    explanation: "內容含有加入群組、明牌或保證獲利等語句，建議提高警覺。",
  },
  incomplete_information: {
    label: "資訊不完整",
    explanation: "此內容缺乏完整資料來源，需搭配其他來源確認。",
  },
};

export const sourceComparisonIntro: Record<SourceType, string> = {
  x: "社群貼文可反映即時討論，但不一定代表事實。系統會將貼文內容與新聞及官方公告進行比對，以判斷是否存在可信度風險。",
  yahoo: "相關新聞可協助理解事件脈絡，但不代表所有內容皆已被官方確認。",
  mops: "",
};

export function mopsComparisonText(hasAnnouncement: boolean, target: string) {
  if (hasAnnouncement) {
    return {
      text: `公開資訊觀測站已找到與「${target}」相關的公告，可作為本事件的官方查證來源。建議使用者查看公告原文，以確認新聞或社群內容是否正確引用。`,
      statusLabel: "官方已確認／可佐證",
    };
  }
  return {
    text: "目前公開資訊觀測站尚未找到可直接支持該說法的公告。此狀態不代表該資訊一定為假，但表示仍需要更多來源佐證。",
    statusLabel: "暫無官方佐證／待查證",
  };
}

export const investmentExperienceLabels: Record<InvestmentExperience, string> = {
  beginner: "投資新手",
  experienced: "有經驗",
  news_only: "只看財經新聞",
};

export const watchedMarketLabels: Record<WatchedMarket, string> = {
  tw_stock: "台股",
  us_stock: "美股",
  etf: "ETF",
  industry_news: "產業新聞",
};

export const alertFrequencyLabels: Record<AlertFrequency, string> = {
  realtime: "即時提醒",
  daily_digest: "每日摘要",
  high_risk_only: "僅高風險提醒",
};

export const alertTypePrefLabels: Record<AlertTypePref, string> = {
  suspected_false: "疑似假訊息",
  pending_verification: "待查證",
  source_inconsistent: "多來源不一致",
  official_update: "官方查證更新",
};

export const pushTemplateTypeLabels: Record<PushTemplateType, string> = {
  credibility_risk: "可信度風險",
  pending_verification: "待查證",
  source_inconsistent: "來源不一致",
  official_update: "官方查證",
  personalized_digest: "追蹤摘要",
};

interface PushTemplateParams {
  target: string;
  verificationStatus?: string;
  timeWindow?: string;
}

export const pushTemplates: Record<
  PushTemplateType,
  (params: PushTemplateParams) => string
> = {
  credibility_risk: ({ target, verificationStatus }) =>
    `【可信度風險】你追蹤的「${target}」出現待查證資訊\n系統偵測到與「${target}」相關的內容可信度風險偏高，目前查證狀態為「${verificationStatus ?? "待查證"}」。建議查看多來源查證結果與原始資料。\n${pushDisclaimerSuffix}`,
  pending_verification: ({ target, timeWindow }) =>
    `【待查證】「${target}」相關消息尚未取得足夠佐證\n近 ${timeWindow ?? "24 小時"} 內，系統偵測到相關討論或新聞，但目前尚未找到足夠官方或可靠來源支持。\n${pushDisclaimerSuffix}`,
  source_inconsistent: ({ target }) =>
    `【來源不一致】你追蹤的「${target}」出現不同說法\n系統比對多個來源後，發現同一事件的描述存在差異，建議查看各來源摘要與原始連結。\n${pushDisclaimerSuffix}`,
  official_update: ({ target }) =>
    `【官方查證】「${target}」已有官方資料可參考\n系統偵測到公開資訊觀測站出現相關公告，可作為本事件的官方查證來源。\n${pushDisclaimerSuffix}`,
  personalized_digest: ({ target, timeWindow }) =>
    `【追蹤摘要】你關注的「${target}」有新的可信度風險更新\n系統已整理近 ${timeWindow ?? "7 天"} 的模型判斷與多來源查證結果，建議查看最新狀態。\n${pushDisclaimerSuffix}`,
};

export const authCopy = {
  loginTitle: "登入後追蹤你的關注標的",
  loginSubtitle:
    "設定公司、股票代號、產業與關鍵字，系統將在相關資訊出現可信度風險或查證狀態更新時提醒你。",
  registerConfirmation:
    "建議先加入 3–5 個追蹤標的。當相關資訊出現可信度風險、缺乏官方佐證或來源不一致時，系統會主動提醒你。",
};

export const dashboardCopy = {
  title: "金融資訊可信度風險總覽",
  subtitle:
    "整合 X、Yahoo 財經新聞與公開資訊觀測站，協助判斷財經資訊是否可信、是否需要查證。",
};

export const verifyCopy = {
  title: "快速查證金融資訊",
  subtitle:
    "輸入關鍵字、公司名稱、股票代號，或貼上新聞／貼文網址，系統將進行真偽輔助判斷與多來源查證。",
};

export const modelJudgmentTermLabel = "模型輔助判斷結果";
