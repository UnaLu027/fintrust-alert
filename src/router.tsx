import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { DashboardPage } from "./pages/DashboardPage";
import { QuickVerifyPage } from "./pages/QuickVerifyPage";
import { AnalysisResultPage } from "./pages/AnalysisResultPage";
import { AlertsCenterPage } from "./pages/AlertsCenterPage";
import { HistoryPage } from "./pages/HistoryPage";
import { AboutDisclaimerPage } from "./pages/AboutDisclaimerPage";
import { SettingsPage } from "./pages/SettingsPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  {
    path: "/",
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: "dashboard", element: <DashboardPage /> },
          { path: "verify", element: <QuickVerifyPage /> },
          { path: "analysis/:id", element: <AnalysisResultPage /> },
          { path: "alerts", element: <AlertsCenterPage /> },
          { path: "history", element: <HistoryPage /> },
          { path: "about", element: <AboutDisclaimerPage /> },
          { path: "settings", element: <SettingsPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
