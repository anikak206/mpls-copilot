import { createPortal } from "react-dom";
import { X } from "lucide-react";

export const Pill = ({ value, testid }) => (
  <span className={`pill pill-${value}`} data-testid={testid}>{String(value ?? "—").replace(/_/g, " ")}</span>
);

export const PageHeader = ({ title, subtitle, children }) => (
  <div className="page-head">
    <div>
      <h1 data-testid="page-title">{title}</h1>
      {subtitle && <p>{subtitle}</p>}
    </div>
    {children && <div className="btn-row">{children}</div>}
  </div>
);

export const Stat = ({ label, value, foot, icon: Icon, testid }) => (
  <div className="stat" data-testid={testid}>
    <span className="stat-label">{Icon && <Icon size={14} />}{label}</span>
    <span className="stat-value">{value}</span>
    {foot && <span className="stat-foot">{foot}</span>}
  </div>
);

export function Pager({ page, total, pageSize, setPage, testid = "pager" }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="pager" data-testid={testid}>
      <span data-testid={`${testid}-info`}>{total} records · page {page} of {pages}</span>
      <div className="btn-row">
        <button className="btn ghost sm" disabled={page <= 1} onClick={() => setPage(page - 1)} data-testid={`${testid}-prev`}>Previous</button>
        <button className="btn ghost sm" disabled={page >= pages} onClick={() => setPage(page + 1)} data-testid={`${testid}-next`}>Next</button>
      </div>
    </div>
  );
}

export function Modal({ open, title, onClose, children, wide, testid = "modal" }) {
  if (!open) return null;
  return createPortal(
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()} data-testid={`${testid}-overlay`}>
      <div className={`modal ${wide ? "wide" : ""}`} role="dialog" aria-modal="true" aria-label={title} data-testid={testid}>
        <div className="modal-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Close" data-testid={`${testid}-close`}><X size={16} /></button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>,
    document.body,
  );
}

export const Field = ({ label, error, children, full }) => (
  <div className={`field ${full ? "full" : ""}`}>
    <label>{label}</label>
    {children}
    {error && <span className="field-error">{error}</span>}
  </div>
);

export const Select = ({ value, onChange, options, placeholder, testid, ...rest }) => (
  <select className="select" value={value ?? ""} onChange={(e) => onChange(e.target.value)} data-testid={testid} {...rest}>
    {placeholder !== undefined && <option value="">{placeholder}</option>}
    {options.map((o) => {
      const [v, l] = Array.isArray(o) ? o : [o, String(o).replace(/_/g, " ")];
      return <option key={v} value={v}>{l}</option>;
    })}
  </select>
);

export const ErrorBox = ({ error, testid = "error-box" }) => (error ? <div className="alert-box" data-testid={testid}>{error}</div> : null);

export function DataTable({ columns, rows, loading, rowKey, onRowClick, testid = "data-table" }) {
  return (
    <div className="table-wrap">
      <table className="tbl" data-testid={testid}>
        <thead><tr>{columns.map((c) => <th key={c.key} className={c.hideSm ? "hide-sm" : ""}>{c.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[rowKey]} className={onRowClick ? "clickable" : ""} onClick={onRowClick ? () => onRowClick(row) : undefined} data-testid={`${testid}-row-${row[rowKey]}`}>
              {columns.map((c) => (
                <td key={c.key} className={`${c.num ? "num" : ""} ${c.hideSm ? "hide-sm" : ""}`}>{c.render ? c.render(row) : row[c.key] ?? "—"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!loading && rows.length === 0 && <div className="empty" data-testid={`${testid}-empty`}>No records match the current filters.</div>}
      {loading && rows.length === 0 && <div className="empty">Loading…</div>}
    </div>
  );
}
