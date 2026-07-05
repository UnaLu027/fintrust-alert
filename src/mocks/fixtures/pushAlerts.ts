import type { PushAlert } from "../../types";
import { pushTemplates } from "../../content/copy";
import { demoUser } from "./users";

/**
 * Push-eligibility rule (baked statically here, not computed at runtime):
 * an alert only exists when (a) relatedTarget matches the user's watchlist,
 * (b) riskLevel is medium/high OR verificationStatus just became
 * official_confirmed/inconsistent, and (c) there is no duplicate for the
 * same analysisId + templateType. All 4 demo analyses satisfy (a) since the
 * demo user watches 台積電/2330/鴻海/2317.
 */
export const demoPushAlerts: PushAlert[] = [
  {
    id: "push-001",
    userId: demoUser.id,
    templateType: "credibility_risk",
    title: "台積電即將暴跌，內線消息外流？X 貼文瘋傳",
    relatedTarget: "台積電",
    riskLevel: "high",
    verificationStatus: "suspected_false",
    reason: "與追蹤標的「台積電」相關，且模型判斷可信度風險偏高",
    message: pushTemplates.credibility_risk({
      target: "台積電",
      verificationStatus: "疑似假訊息",
    }),
    createdAt: "2026-07-06T08:15:00+08:00",
    analysisId: "demo-tsmc-crash-rumor",
  },
  {
    id: "push-002",
    userId: demoUser.id,
    templateType: "pending_verification",
    title: "台積電 Q2 營收將暴增 50%？法人：目標價上看 1000 元",
    relatedTarget: "台積電",
    riskLevel: "high",
    verificationStatus: "pending",
    reason: "與追蹤關鍵字「財報」相關，目前尚未取得足夠官方佐證",
    message: pushTemplates.pending_verification({
      target: "台積電",
      timeWindow: "24 小時",
    }),
    createdAt: "2026-07-05T22:35:00+08:00",
    analysisId: "demo-q2-revenue-surge",
  },
  {
    id: "push-003",
    userId: demoUser.id,
    templateType: "source_inconsistent",
    title: "鴻海海外新廠傳出投產延宕，法人看法分歧",
    relatedTarget: "鴻海",
    riskLevel: "medium",
    verificationStatus: "inconsistent",
    reason: "與追蹤標的「鴻海」相關，且 X 與 Yahoo 財經說法不一致",
    message: pushTemplates.source_inconsistent({ target: "鴻海" }),
    createdAt: "2026-07-06T10:10:00+08:00",
    analysisId: "demo-multi-source-conflict",
  },
  {
    id: "push-004",
    userId: demoUser.id,
    templateType: "official_update",
    title: "台積電公開資訊觀測站公告：Q2 法說會重大訊息，資本支出上修",
    relatedTarget: "台積電",
    riskLevel: "low",
    verificationStatus: "official_confirmed",
    reason: "公開資訊觀測站出現與「台積電」相關的新公告",
    message: pushTemplates.official_update({ target: "台積電" }),
    createdAt: "2026-07-04T16:25:00+08:00",
    analysisId: "demo-mops-confirmed",
  },
  {
    id: "push-005",
    userId: demoUser.id,
    templateType: "personalized_digest",
    title: "本週台積電、鴻海追蹤摘要",
    relatedTarget: "台積電、鴻海",
    riskLevel: "medium",
    verificationStatus: "pending",
    reason: "追蹤標的近 7 天可信度風險更新彙整",
    message: pushTemplates.personalized_digest({
      target: "台積電、鴻海",
      timeWindow: "7 天",
    }),
    createdAt: "2026-07-06T09:00:00+08:00",
    analysisId: "demo-q2-revenue-surge",
  },
];
