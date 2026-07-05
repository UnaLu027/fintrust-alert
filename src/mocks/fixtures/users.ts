import type { User } from "../../types";

export const demoUser: User = {
  id: "user-demo-001",
  email: "demo@fintrust.app",
  investmentExperience: "beginner",
  watchedMarkets: ["tw_stock", "industry_news"],
  watchedCompanies: ["台積電", "2330", "鴻海", "2317"],
  watchedIndustries: ["AI", "半導體"],
  watchedKeywords: ["財報", "重大訊息", "暴跌", "爆料", "假新聞"],
  alertFrequency: "high_risk_only",
  alertTypes: [
    "suspected_false",
    "pending_verification",
    "source_inconsistent",
    "official_update",
  ],
  createdAt: "2026-06-20T09:00:00+08:00",
};

/** demo password for the mock login handler; never used for anything real */
export const demoPassword = "demo1234";
