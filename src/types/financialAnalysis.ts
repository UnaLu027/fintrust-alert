export type RuleSeverity =
  | "positive"
  | "normal"
  | "attention"
  | "high_attention"
  | "data_issue"
  | "insufficient_data";

export interface SourceCoverage {
  source_name: string;
  source_url: string;
  status: "available" | "missing" | "error";
  report_period?: string;
  fields_found: string[];
  fields_missing: string[];
}

export interface NormalizedFinancialStatement {
  ticker: string;
  company_name: string;
  industry: "半導體";
  subindustry: string;
  report_period?: string;
  monthly_revenue_period?: string;
  revenue?: number;
  gross_profit?: number;
  operating_income?: number;
  net_income?: number;
  eps?: number;
  cash_and_cash_equivalents?: number;
  inventory?: number;
  current_assets?: number;
  total_assets?: number;
  current_liabilities?: number;
  total_liabilities?: number;
  equity?: number;
  monthly_revenue?: number;
  previous_month_revenue?: number;
  prior_year_month_revenue?: number;
  monthly_revenue_mom_reported?: number;
  monthly_revenue_yoy_reported?: number;
  currency_unit: string;
  source_coverage: SourceCoverage[];
  data_quality_warnings: string[];
}

export interface CalculatedMetric {
  code: string;
  label: string;
  category: string;
  value: number;
  unit: string;
  formula: string;
  inputs: Record<string, number>;
  source_fields: string[];
}

export interface RuleResult {
  rule_id: string;
  name: string;
  category: string;
  severity: RuleSeverity;
  triggered: boolean;
  metric_code: string;
  actual_value?: number;
  unit?: string;
  threshold_description: string;
  explanation: string;
  evidence_metrics: string[];
}

export interface FinancialStatementAnalysisReport {
  ticker: string;
  company_name: string;
  industry: "半導體";
  subindustry: string;
  report_period?: string;
  monthly_revenue_period?: string;
  analyzed_at: string;
  rule_version: string;
  threshold_basis: string;
  overall_severity: RuleSeverity;
  summary: string;
  statement: NormalizedFinancialStatement;
  metrics: CalculatedMetric[];
  rule_results: RuleResult[];
  limitations: string[];
}

export interface HistoricalPeriodRecord {
  ticker: string;
  company_name: string;
  subindustry: string;
  fiscal_year: number;
  roc_year: number;
  quarter: 4;
  period: string;
  source_name: string;
  source_url: string;
  status: "available" | "missing" | "error";
  revenue?: number;
  gross_profit?: number;
  operating_income?: number;
  net_income?: number;
  eps?: number;
  cash_and_cash_equivalents?: number;
  inventory?: number;
  current_assets?: number;
  total_assets?: number;
  current_liabilities?: number;
  total_liabilities?: number;
  equity?: number;
  operating_cash_flow?: number;
  investing_cash_flow?: number;
  capital_expenditure?: number;
  research_and_development_expense?: number;
  currency_unit: string;
  fields_found: string[];
  fields_missing: string[];
  concept_matches: Record<string, string>;
  warnings: string[];
}

export interface HistoricalTrendMetric {
  code: string;
  label: string;
  category: string;
  unit: string;
  period_values: Record<string, number>;
  latest_value?: number;
  previous_value?: number;
  change_percent?: number;
  change_percentage_points?: number;
  formula: string;
  source_fields: string[];
}

export interface HistoricalRuleResult {
  rule_id: string;
  name: string;
  category: string;
  severity: RuleSeverity;
  triggered: boolean;
  explanation: string;
  threshold_description: string;
  evidence_periods: string[];
  evidence_metrics: string[];
  rule_scope: string;
  logic_expression?: string;
  actual_values: Record<string, number | null>;
}

export interface HistoricalFinancialAnalysisReport {
  ticker: string;
  company_name: string;
  industry: "半導體";
  subindustry: string;
  requested_years: number;
  available_years: number;
  start_year?: number;
  end_year?: number;
  analyzed_at: string;
  source_method: string;
  rule_version: string;
  threshold_basis: string;
  overall_severity: RuleSeverity;
  summary: string;
  periods: HistoricalPeriodRecord[];
  trend_metrics: HistoricalTrendMetric[];
  rule_results: HistoricalRuleResult[];
  limitations: string[];
}

export interface FrontendMetricCard {
  code: string;
  label: string;
  category: string;
  unit: string;
  latest_value?: number;
  previous_value?: number;
  change_percent?: number;
  change_percentage_points?: number;
  formula: string;
  period_values: Record<string, number>;
}

export interface FrontendRuleCard {
  rule_id: string;
  name: string;
  category: string;
  severity: RuleSeverity;
  triggered: boolean;
  explanation: string;
  threshold_description: string;
  evidence_periods: string[];
  evidence_metrics: string[];
  rule_scope: string;
  logic_expression?: string;
  actual_values: Record<string, number | null>;
}

export interface FrontendSourceItem {
  source_name: string;
  source_url: string;
  period?: string;
  status: string;
}

export interface FrontendAnalysisSnapshot {
  schema_version: string;
  analysis_run_id: string;
  ticker: string;
  company_name: string;
  industry: "半導體";
  subindustry: string;
  generated_at: string;
  data_updated_at: string;
  overall_severity: RuleSeverity;
  summary: string;
  rule_version: string;
  threshold_basis: string;
  key_metrics: FrontendMetricCard[];
  rule_cards: FrontendRuleCard[];
  sources: FrontendSourceItem[];
  limitations: string[];
}
