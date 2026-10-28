import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  Activity, AlertTriangle, BarChart3, BrainCircuit, ClipboardCheck, Database, FileText, Gauge, LifeBuoy,
  LogOut, Menu, Router, ScrollText, ShieldCheck, Users, Wrench,
} from "lucide-react";
import { ROLES, useAuth } from "../context/AuthContext";

const { ADMIN, ENGINEER, AUDITOR } = ROLES;
const ALL = [ADMIN, ENGINEER, AUDITOR];

export const NAV = [
  { group: "Operations", items: [
    { to: "/", label: "Dashboard", icon: Gauge, roles: ALL, end: true },
    { to: "/devices", label: "Devices", icon: Router, roles: ALL },
    { to: "/telemetry", label: "Telemetry", icon: Activity, roles: ALL },
    { to: "/alerts", label: "Alerts", icon: AlertTriangle, roles: ALL },
    { to: "/incidents", label: "Incidents", icon: LifeBuoy, roles: ALL },
  ]},
  { group: "Intelligence", items: [
    { to: "/predictions", label: "Predictions", icon: BrainCircuit, roles: ALL },
    { to: "/recommendations", label: "Recommendations", icon: ClipboardCheck, roles: ALL },
    { to: "/actions", label: "Actions & Outcomes", icon: Wrench, roles: ALL },
  ]},
  { group: "Governance", items: [
    { to: "/reports", label: "Reports", icon: BarChart3, roles: ALL },
    { to: "/db-lab", label: "Database Lab", icon: Database, roles: ALL },
    { to: "/audit", label: "Audit Logs", icon: ScrollText, roles: [ADMIN, AUDITOR] },
    { to: "/users", label: "Users & Roles", icon: Users, roles: [ADMIN] },
  ]},
];

export default function Layout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const initials = user.full_name.split(" ").map((p) => p[0]).slice(0, 2).join("");
  return (
    <div className="shell">
      <aside className={`sidebar ${open ? "open" : ""}`} data-testid="sidebar">
        <div className="brand">
          <div className="brand-mark"><ShieldCheck size={20} /></div>
          <div>
            <div className="brand-title">MPLS Copilot</div>
            <div className="brand-sub">Air-gapped · Predictive</div>
          </div>
        </div>
        {NAV.map((g) => {
          const items = g.items.filter((i) => i.roles.includes(user.role));
          if (!items.length) return null;
          return (
            <nav className="nav" key={g.group} aria-label={g.group}>
              <span className="nav-label">{g.group}</span>
              {items.map(({ to, label, icon: Icon, end }) => (
                <NavLink key={to} to={to} end={end} onClick={() => setOpen(false)} data-testid={`nav-${to.replace("/", "") || "dashboard"}`}>
                  <Icon size={17} /> {label}
                </NavLink>
              ))}
            </nav>
          );
        })}
        <div className="airgap" data-testid="airgap-indicator">
          <strong><FileText size={14} /> Local inference only</strong>
          ML runs on this server. No telemetry is sent to external AI providers.
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <button className="icon-btn menu-btn" onClick={() => setOpen(!open)} aria-label="Toggle navigation" data-testid="menu-toggle"><Menu size={18} /></button>
          <span className="muted small hide-sm">Air-Gapped Predictive Copilot for Secure MPLS Operations</span>
          <div className="topbar-user">
            <div className="avatar" aria-hidden>{initials}</div>
            <div className="hide-sm">
              <div style={{ fontWeight: 600, fontSize: 14 }} data-testid="current-user-name">{user.full_name}</div>
              <div className="small muted" data-testid="current-user-role">{user.role}</div>
            </div>
            <button className="btn ghost sm" onClick={logout} data-testid="logout-button"><LogOut size={14} /> Sign out</button>
          </div>
        </header>
        <main className="content"><Outlet /></main>
      </div>
    </div>
  );
}
