import { useState } from "react";
import { toast } from "sonner";
import { ROLES, useAuth } from "../context/AuthContext";
import { api, errMsg } from "../lib/api";
import { useFetch } from "../lib/hooks";
import { ErrorBox, PageHeader, Pill } from "../components/kit";

const fmt = (v) => (v === null || v === undefined ? "—" : typeof v === "number" && !Number.isInteger(v) ? v.toFixed(2) : String(v));

function QueryCard({ q, i }) {
  return (
    <div className="card" data-testid={`dblab-query-${i}`} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div className="btn-row" style={{ alignItems: "center" }}><Pill value={q.category.toLowerCase()} /> <strong>{q.title}</strong> <span className="small muted">{q.rows.length} rows</span></div>
      <pre className="sql">{q.sql}</pre>
      <div className="table-wrap" style={{ maxHeight: 240, overflowY: "auto" }}>
        <table className="tbl"><thead><tr>{q.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
          <tbody>{q.rows.slice(0, 10).map((r, j) => <tr key={j}>{q.columns.map((c) => <td key={c} className="num">{fmt(r[c])}</td>)}</tr>)}</tbody></table>
      </div>
    </div>
  );
}

function TransactionDemo() {
  const [result, setResult] = useState(null);
  const run = async (simulate_failure) => {
    try {
      const { data } = await api.post("/db-lab/transaction-demo", { simulate_failure });
      setResult(data);
      toast.success(`Transaction ${data.outcome.replace("_", " ")}`);
    } catch (e) {
      toast.error(errMsg(e));
    }
  };
  return (
    <div className="card aqua" data-testid="transaction-demo">
      <h3 className="section-title">Transaction demo (commit vs rollback)</h3>
      <p className="small" style={{ marginTop: 0 }}>Inserts an incident, a linked alert and an audit row in one transaction. With a simulated failure, all three are rolled back.</p>
      <div className="btn-row">
        <button className="btn" onClick={() => run(false)} data-testid="transaction-commit-button">Run & commit</button>
        <button className="btn danger" onClick={() => run(true)} data-testid="transaction-rollback-button">Run with failure (rollback)</button>
      </div>
      {result && (
        <div style={{ marginTop: 12 }} data-testid="transaction-result">
          <p><Pill value={result.outcome === "committed" ? "resolved" : "critical"} /> <strong>{result.outcome}</strong></p>
          <ul className="timeline">{result.steps.map((s) => <li key={s} className="mono small">{s}</li>)}</ul>
          <p className="small mono">before {JSON.stringify(result.counts_before)}<br />after&nbsp; {JSON.stringify(result.counts_after)}</p>
        </div>
      )}
    </div>
  );
}

export default function DbLab() {
  const { hasRole } = useAuth();
  const { data, error } = useFetch("/db-lab/queries");
  return (
    <>
      <PageHeader title="Database Lab" subtitle="Live results of JOIN, aggregate, view and stored-procedure queries executed against MySQL." />
      <ErrorBox error={error} />
      {data && (
        <div className="grid grid-2" style={{ marginBottom: 16, alignItems: "start" }}>
          <div className="card" data-testid="db-objects">
            <h3 className="section-title">Database objects in this schema</h3>
            <ul className="timeline">{data.database_objects.map((o) => <li key={o.name}><Pill value={o.kind.toLowerCase()} /> <span className="mono">{o.name}</span> <span className="small muted">{o.detail}</span></li>)}</ul>
          </div>
          {hasRole(ROLES.ADMIN) ? <TransactionDemo /> : <div className="card note-box">Transaction demo is available to Administrators.</div>}
        </div>
      )}
      <div className="grid grid-2">{data?.queries.map((q, i) => <QueryCard key={q.title} q={q} i={i} />)}</div>
    </>
  );
}
