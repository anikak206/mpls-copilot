import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import "./App.css";
import Layout from "./components/Layout";
import { AuthProvider, ROLES, useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Devices from "./pages/Devices";
import Telemetry from "./pages/Telemetry";
import Alerts from "./pages/Alerts";
import Incidents from "./pages/Incidents";
import Predictions from "./pages/Predictions";
import Recommendations from "./pages/Recommendations";
import Actions from "./pages/Actions";
import Reports from "./pages/Reports";
import DbLab from "./pages/DbLab";
import AuditLogs from "./pages/AuditLogs";
import UsersPage from "./pages/Users";

function Protected({ roles, children }) {
  const { user } = useAuth();
  if (user === null) return <div className="empty" data-testid="auth-loading">Checking session…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) {
    return <div className="card" data-testid="forbidden-page"><h2>Access denied</h2><p className="muted">Your role ({user.role}) cannot open this page.</p></div>;
  }
  return children;
}

function LoginRoute() {
  const { user } = useAuth();
  return user ? <Navigate to="/" replace /> : <Login />;
}

export default function App() {
  const { ADMIN, AUDITOR } = ROLES;
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginRoute />} />
          <Route element={<Protected><Layout /></Protected>}>
            <Route index element={<Dashboard />} />
            <Route path="devices" element={<Devices />} />
            <Route path="telemetry" element={<Telemetry />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="incidents" element={<Incidents />} />
            <Route path="predictions" element={<Predictions />} />
            <Route path="recommendations" element={<Recommendations />} />
            <Route path="actions" element={<Actions />} />
            <Route path="reports" element={<Reports />} />
            <Route path="db-lab" element={<DbLab />} />
            <Route path="audit" element={<Protected roles={[ADMIN, AUDITOR]}><AuditLogs /></Protected>} />
            <Route path="users" element={<Protected roles={[ADMIN]}><UsersPage /></Protected>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" richColors closeButton />
    </AuthProvider>
  );
}
