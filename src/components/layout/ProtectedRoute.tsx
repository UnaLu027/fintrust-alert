import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { LoadingState } from "../common/LoadingState";

export function ProtectedRoute() {
  const { user, isInitializing } = useAuth();

  if (isInitializing) {
    return <LoadingState label="正在確認登入狀態..." />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
