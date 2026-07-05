import type { RiskLevel } from "../types";

const paragraphs: Record<RiskLevel, string> = {
  high:
    "此內容包含高強度投資用語，且目前尚未找到足夠官方來源佐證。模型判斷其可信度風險偏高，建議使用者查看多來源查證結果與原始連結後再自行判斷。",
  medium:
    "此內容部分描述仍需進一步查證。系統已偵測到相關新聞或社群討論，但目前來源間資訊尚未完全一致，建議搭配官方公告或其他可信來源確認。",
  low:
    "此內容目前未偵測到明顯可信度風險，且已有部分來源可互相佐證。不過本系統結果仍僅供資訊整理，建議使用者保留自主判斷。",
};

export function riskExplanationParagraph(level: RiskLevel): string {
  return paragraphs[level];
}

const qualitativeState: Record<RiskLevel, string> = {
  high: "偏高，需進一步查證",
  medium: "中等，建議搭配其他來源確認",
  low: "偏低，已有部分來源可互相佐證",
};

/**
 * Renders the "可信度狀態" line. Never emit a raw score/percentage here —
 * riskScore stays an internal-only number, UI always speaks in qualitative terms.
 */
export function modelJudgmentPhrasing(level: RiskLevel): string {
  return `可信度狀態：${qualitativeState[level]}`;
}

export const riskLevelLabel: Record<RiskLevel, string> = {
  low: "低",
  medium: "中",
  high: "高",
};
