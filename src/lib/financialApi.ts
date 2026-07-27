const configuredFinancialApiBase = import.meta.env.VITE_FINANCIAL_API_BASE_URL?.trim();

export const financialApiBase = (
  configuredFinancialApiBase || (import.meta.env.DEV ? "http://localhost:8000" : "")
).replace(/\/$/, "");

export function financialApiUrl(path: string): string {
  if (!financialApiBase) {
    throw new Error(
      "部署設定缺少 VITE_FINANCIAL_API_BASE_URL；請先填入 Cloud Run 後端網址再重新建置前端。",
    );
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${financialApiBase}${normalizedPath}`;
}
