import { Link } from "react-router-dom";
import { Activity, AlertTriangle, BrainCircuit, LifeBuoy, Router } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useFetch } from "../lib/hooks";
import { fmtDate } from "../lib/api";
import { ErrorBox, PageHeader, Pill, Stat } from "../components/kit";

const RISK_COLORS = { low: "#7FB89A", medium: "#E3B75A", high: "#E08A5C", critical: "#C9505D" };
const STATUS_COLORS = { up: "#A8D1D1", degraded: "#E3B75A", down: "#C9505D", maintenance: "#9AA8AB" };
const sum = (o) => Object.values(o || {}).reduce((a, b) => a + b, 0);
const toSeries = (o, order) => order.filter((k) => o?.[k]).map((k) => ({ name: k, value: o[k] }));

const legendText = (v) => <span style={{ color: "#263238" }}>{v}</span>;
const localHour = (utc) => new Date(`${utc.replace(" ", "T")}:00Z`).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

function TrendChart({ data }) {
  return (
    <div className="card span-2" data-testid="telemetry-trend-chart">
      <h3 className="section-title">Network telemetry · hourly averages (7 days, local time)</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data.map((d) => ({ ...d, hour: localHour(d.date) }))} margin={{ left: -10, right: 10 }}>
          <CartesianGrid stroke="#D4E1E1" strokeDasharray="3 3" />
          <XAxis dataKey="hour" tick={{ fontSize: 11, fill: "#667477" }} interval={5} />
          <YAxis yAxisId="l" tick={{ fontSize: 11, fill: "#667477" }} />
          <YAxis yAxisId="r" orientation="right" tick={{ fontSize: 11, fill: "#667477" }} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} formatter={legendText} />
          <Line yAxisId="l" type="monotone" dataKey="latency" name="Latency (ms)" stroke="#2F5F5F" dot={false} strokeWidth={2} />
          <Line yAxisId="l" type="monotone" dataKey="cpu" name="CPU (%)" stroke="#8FC1C1" dot={false} strokeWidth={2} />
          <Line yAxisId="r" type="monotone" dataKey="loss" name="Loss (%)" stroke="#C9505D" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function Donut({ title, data, colors, testid }) {
  return (
    <div className="card" data-testid={testid}>
      <h3 className="section-title">{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
            {data.map((d) => <Cell key={d.name} fill={colors[d.name] || "#A8D1D1"} />)}
          </Pie>
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} formatter={legendText} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

function RecentList({ title, items, render, link, testid }) {
  return (
    <div className="card" data-testid={testid}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h3 className="section-title">{title}</h3>
        {link && <Link to={link} className="small">View all</Link>}
      </div>
      <ul className="timeline">{items.length ? items.map(render) : <li className="muted">Nothing yet.</li>}</ul>
    </div>
  );
}

export default function Dashboard() {
  const { data, error } = useFetch("/dashboard/summary");
  if (error) return <ErrorBox error={error} />;
  if (!data) return <div className="empty">Loading dashboard…</div>;
  const alertsOpen = sum(data.open_alerts_by_severity);
  const incidentsOpen = sum(data.incidents_by_status) - (data.incidents_by_status.closed || 0);
  const severityBars = ["info", "warning", "major", "critical"].map((s) => ({ name: s, count: data.open_alerts_by_severity[s] || 0 }));
  return (
    <>
      <PageHeader title="Operations dashboard" subtitle="Live view of device health, alerts, incidents and local ML risk assessments." />
      <div className="grid grid-4" style={{ marginBottom: 16 }}>
        <Stat icon={Router} label="Devices" value={sum(data.devices_by_status)} foot={`${data.devices_by_status.up || 0} up · ${data.devices_by_status.degraded || 0} degraded · ${data.devices_by_status.down || 0} down`} testid="stat-devices" />
        <Stat icon={AlertTriangle} label="Active alerts" value={alertsOpen} foot={`${data.open_alerts_by_severity.critical || 0} critical`} testid="stat-alerts" />
        <Stat icon={LifeBuoy} label="Open incidents" value={incidentsOpen} foot={Object.entries(data.incidents_by_status).map(([k, v]) => `${v} ${k}`).join(" · ") || "none"} testid="stat-incidents" />
        <Stat icon={BrainCircuit} label="Avg risk score" value={data.avg_risk} foot={`${sum(data.label_distribution)} predictions · ${data.label_distribution.anomalous || 0} anomalous`} testid="stat-risk" />
      </div>
      <div className="grid grid-3" style={{ marginBottom: 16 }}>
        <TrendChart data={data.telemetry_series} />
        <Donut title="Risk distribution" data={toSeries(data.risk_distribution, ["low", "medium", "high", "critical"])} colors={RISK_COLORS} testid="risk-distribution-chart" />
      </div>
      <div className="grid grid-3" style={{ marginBottom: 16 }}>
        <Donut title="Device status" data={toSeries(data.devices_by_status, ["up", "degraded", "down", "maintenance"])} colors={STATUS_COLORS} testid="device-status-chart" />
        <div className="card" data-testid="alert-severity-chart">
          <h3 className="section-title">Active alerts by severity</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={severityBars}><CartesianGrid stroke="#D4E1E1" strokeDasharray="3 3" /><XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis allowDecimals={false} tick={{ fontSize: 11 }} /><Tooltip /><Bar dataKey="count" fill="#A8D1D1" radius={[6, 6, 0, 0]} /></BarChart>
          </ResponsiveContainer>
        </div>
        <RecentList title="Recent activity" testid="recent-activity" items={data.recent_activity} render={(a) => (
          <li key={a.audit_id}><strong>{a.action.replace(/_/g, " ")}</strong> <span className="muted">· {a.user_email || "system"} · {fmtDate(a.created_at)}</span></li>
        )} />
      </div>
      <div className="grid grid-2">
        <RecentList title="Recent predictions" link="/predictions" testid="recent-predictions" items={data.recent_predictions} render={(p) => (
          <li key={p.prediction_id}><Pill value={p.label} /> <strong>{p.hostname}</strong> <span className="mono">risk {p.risk_score}</span> <span className="muted small">· {fmtDate(p.created_at)}</span></li>
        )} />
        <RecentList title="Recent alerts" link="/alerts" testid="recent-alerts" items={data.recent_alerts} render={(a) => (
          <li key={a.alert_id}><Pill value={a.severity} /> <strong>{a.hostname}</strong> <span className="small">{a.message}</span></li>
        )} />
      </div>
      <p className="small muted" style={{ marginTop: 16 }}><Activity size={12} /> Engineers see data for their assigned devices only.</p>
    </>
  );
}
