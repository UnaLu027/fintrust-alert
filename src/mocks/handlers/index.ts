import { authHandlers } from "./auth";
import { dashboardHandlers } from "./dashboard";
import { verifyHandlers } from "./verify";
import { analysisHandlers } from "./analysis";
import { alertsHandlers } from "./alerts";
import { historyHandlers } from "./history";
import { watchlistHandlers } from "./watchlist";

export const handlers = [
  ...authHandlers,
  ...dashboardHandlers,
  ...verifyHandlers,
  ...analysisHandlers,
  ...alertsHandlers,
  ...historyHandlers,
  ...watchlistHandlers,
];
