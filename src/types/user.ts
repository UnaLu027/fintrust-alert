export type InvestmentExperience = "beginner" | "experienced" | "news_only";

export type WatchedMarket = "tw_stock" | "us_stock" | "etf" | "industry_news";

export type AlertFrequency = "realtime" | "daily_digest" | "high_risk_only";

export type AlertTypePref =
  | "suspected_false"
  | "pending_verification"
  | "source_inconsistent"
  | "official_update";

export interface User {
  id: string;
  email: string;
  investmentExperience: InvestmentExperience;
  watchedMarkets: WatchedMarket[];
  watchedCompanies: string[];
  watchedIndustries: string[];
  watchedKeywords: string[];
  alertFrequency: AlertFrequency;
  alertTypes: AlertTypePref[];
  createdAt: string;
}

export interface WatchlistItem {
  id: string;
  userId: string;
  type: "company" | "industry" | "keyword";
  value: string;
  ticker?: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  investmentExperience: InvestmentExperience;
  watchedMarkets: WatchedMarket[];
  watchedCompanies: string[];
  watchedIndustries: string[];
  watchedKeywords: string[];
  alertFrequency: AlertFrequency;
  alertTypes: AlertTypePref[];
}

export interface LoginPayload {
  email: string;
  password: string;
}
