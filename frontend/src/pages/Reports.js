import { useEffect, useState } from "react";
import { Download, FileText } from "lucide-react";
import { toast } from "sonner";
import { api, cleanParams, downloadFile, errMsg } from "../lib/api";
import { useDevices } from "../lib/hooks";
import { ErrorBox, Field, PageHeader, Select } from "../components/kit";

const FILTERS = {
  "device-health": ["status", "latest_risk_level", "device_id"],
  predictions: ["label", "risk_level", "device_id", "date_from", "date_to"],
  "risk-summary": ["days"],
  alerts: ["status", "severity", "device_id", "date_from", "date_to"],
};
const OPTIONS = {
  status: { "device-health": ["up", "degraded", "down", "maintenance"], alerts: ["open", "acknowledged", "resolved"] },
  latest_risk_level: ["low", "medium", "high", "critical"], risk_level: ["low", "medium", "high", "critical"],
  label: ["normal", "uncertain", "anomalous"], severity: ["info", "warning", "major", "critical"],
};
const fmt = (v) => (v === null || v === undefined ? "—" : typeof v === "number" ? (Number.isInteger(v) ? v : v.toFixed(2)) : String(v));

export default function Reports() {
  const devices = useDevices();
  const [report, setReport] = useState("device-health");
  const [filters, setFilters] = useState({ days: 7 });
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const allowed = FILTERS[report];
    const params = cleanParams(Object.fromEntries(Object.entries(filters).filter(([k]) => allowed.includes(k))));
    api.get(`/reports/${report}`, { params }).then((r) => { setData(r.data); setError(""); }).catch((e) => setError(errMsg(e)));
  }, [report, filters]);

  const set = (k) => (v) => setFilters({ ...filters, [k]: v });
  const exportAs = async (format) => {
    try {
      const allowed = FILTERS[report];
      await downloadFile(`/reports/${report}/export`, { format, ...Object.fromEntries(Object.entries(filters).filter(([k]) => allowed.includes(k))) }, `${report}.${format}`);
      toast.success(`${format.toUpperCase()} downloaded`);
    } catch (e) {
      toast.error(errMsg(e));
    }
  };
  const renderFilter = (k) => {
    if (k === "device_id") return <Select key={k} value={filters.device_id} onChange={set(k)} placeholder="All devices" options={devices.map((d) => [d.device_id, d.hostname])} testid="report-device-filter" />;
    if (k === "days") return <Field key={k} label="Window (days)"><input className="input" type="number" min="1" max="365" value={filters.days} onChange={(e) => set("days")(e.target.value)} data-testid="report-days-filter" /></Field>;
    if (k.startsWith("date_")) return <Field key={k} label={k === "date_from" ? "From" : "To"}><input className="input" type="datetime-local" value={filters[k] || ""} onChange={(e) => set(k)(e.target.value)} data-testid={`report-${k}-filter`} /></Field>;
    const opts = k === "status" ? OPTIONS.status[report] : OPTIONS[k];
    return <Select key={k} value={filters[k]} onChange={set(k)} placeholder={`Any ${k.replace(/_/g, " ")}`} options={opts} testid={`report-${k}-filter`} />;
  };

  return (
    <>
      <PageHeader title="Reports" subtitle="Built on MySQL views, JOIN queries and a stored procedure. Export as CSV or PDF.">
        <button className="btn ghost" onClick={() => exportAs("csv")} data-testid="export-csv-button"><Download size={15} /> CSV</button>
        <button className="btn" onClick={() => exportAs("pdf")} data-testid="export-pdf-button"><FileText size={15} /> PDF</button>
      </PageHeader>
      <div className="toolbar">
        <Select value={report} onChange={(v) => { setReport(v); setData(null); }} options={[["device-health", "Device health (view)"], ["predictions", "Prediction report (view)"], ["risk-summary", "Risk summary (stored procedure)"], ["alerts", "Alert report (JOIN)"]]} testid="report-select" />
        {FILTERS[report].map(renderFilter)}
      </div>
      <ErrorBox error={error} />
      {data && (
        <>
          <p className="small muted" data-testid="report-count">{data.title} · {data.count} rows</p>
          <div className="table-wrap">
            <table className="tbl" data-testid="report-table">
              <thead><tr>{data.columns.map((c) => <th key={c}>{c.replace(/_/g, " ")}</th>)}</tr></thead>
              <tbody>{data.rows.slice(0, 200).map((r, i) => <tr key={i}>{data.columns.map((c) => <td key={c} className={typeof r[c] === "number" ? "num" : ""}>{fmt(r[c])}</td>)}</tr>)}</tbody>
            </table>
            {!data.rows.length && <div className="empty">No rows for these filters.</div>}
          </div>
        </>
      )}
    </>
  );
}
