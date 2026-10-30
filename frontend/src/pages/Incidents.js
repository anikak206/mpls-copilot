import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { ROLES, useAuth } from "../context/AuthContext";
import { api, errMsg, fmtDate } from "../lib/api";
import { useDevices, useFetch, useList } from "../lib/hooks";
import { DataTable, ErrorBox, Field, Modal, PageHeader, Pager, Pill, Select } from "../components/kit";

const SEVERITIES = ["info", "warning", "major", "critical"];
const STATUSES = ["open", "investigating", "mitigated", "closed"];

function IncidentForm({ devices, onSaved, onClose }) {
  const [form, setForm] = useState({ device_id: "", title: "", description: "", severity: "major" });
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    if (!form.device_id || form.title.trim().length < 3 || form.description.trim().length < 3) return setError("Device, title and description are required");
    try {
      await api.post("/incidents", { ...form, device_id: Number(form.device_id) });
      toast.success("Incident opened");
      onSaved();
    } catch (err) {
      setError(errMsg(err));
    }
  };
  return (
    <form className="form-grid" onSubmit={submit} noValidate data-testid="incident-form">
      <div className="full"><ErrorBox error={error} testid="incident-form-error" /></div>
      <Field label="Device"><Select value={form.device_id} onChange={(v) => setForm({ ...form, device_id: v })} placeholder="Select device" options={devices.map((d) => [d.device_id, d.hostname])} testid="incident-device-select" /></Field>
      <Field label="Severity"><Select value={form.severity} onChange={(v) => setForm({ ...form, severity: v })} options={SEVERITIES} testid="incident-severity-select" /></Field>
      <Field label="Title" full><input className="input" maxLength={160} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} data-testid="incident-title-input" /></Field>
      <Field label="Description" full><textarea className="textarea" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} data-testid="incident-description-input" /></Field>
      <div className="full btn-row"><button className="btn" type="submit" data-testid="incident-form-submit">Open incident</button><button className="btn ghost" type="button" onClick={onClose}>Cancel</button></div>
    </form>
  );
}

function IncidentDetail({ id, canWrite, onChanged }) {
  const { data, error, reload } = useFetch(`/incidents/${id}`);
  const engineers = useFetch(canWrite ? "/users/engineers" : "/sites").data || [];
  if (error) return <ErrorBox error={error} />;
  if (!data) return <div className="empty">Loading…</div>;
  const patch = async (body) => {
    try {
      await api.patch(`/incidents/${id}`, body);
      toast.success("Incident updated");
      reload();
      onChanged();
    } catch (e) {
      toast.error(errMsg(e));
    }
  };
  return (
    <div data-testid="incident-detail" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <dl className="kv">
        <div><dt>Device</dt><dd>{data.hostname}</dd></div>
        <div><dt>Severity</dt><dd><Pill value={data.severity} /></dd></div>
        <div><dt>Status</dt><dd><Pill value={data.status} testid="incident-detail-status" /></dd></div>
        <div><dt>Assignee</dt><dd>{data.assignee || "Unassigned"}</dd></div>
        <div><dt>Opened</dt><dd>{fmtDate(data.opened_at)}</dd></div>
        <div><dt>Closed</dt><dd>{fmtDate(data.closed_at)}</dd></div>
      </dl>
      <p style={{ margin: 0 }}>{data.description}</p>
      {canWrite && (
        <div className="toolbar">
          <Field label="Change status"><Select value={data.status} onChange={(v) => patch({ status: v })} options={STATUSES} testid="incident-status-select" /></Field>
          <Field label="Assign engineer"><Select value={data.assigned_to || ""} onChange={(v) => v && patch({ assigned_to: Number(v) })} placeholder="Unassigned" options={engineers.map((u) => [u.user_id, u.full_name])} testid="incident-assign-select" /></Field>
        </div>
      )}
      <div className="grid grid-2">
        <div><h3 className="section-title">Linked alerts ({data.alerts.length})</h3>
          <ul className="timeline">{data.alerts.map((a) => <li key={a.alert_id}><Pill value={a.severity} /> {a.message}</li>)}{!data.alerts.length && <li className="muted">None</li>}</ul></div>
        <div><h3 className="section-title">Engineer actions ({data.actions.length})</h3>
          <ul className="timeline">{data.actions.map((a) => <li key={a.action_id}><strong>{a.action_type.replace(/_/g, " ")}</strong> — {a.description} {a.outcome && <Pill value={a.outcome.result} />}</li>)}{!data.actions.length && <li className="muted">None</li>}</ul></div>
      </div>
      <div><h3 className="section-title">Operational history (audit trail, incl. trigger-recorded status changes)</h3>
        <ul className="timeline" data-testid="incident-history">{data.history.map((h) => <li key={h.audit_id}><strong>{h.action.replace(/_/g, " ")}</strong> {h.details && <span className="mono small">{h.details}</span>} <span className="muted small">· {h.user_email || "system"} · {fmtDate(h.created_at)}</span></li>)}{!data.history.length && <li className="muted">No history yet</li>}</ul></div>
    </div>
  );
}

export default function Incidents() {
  const { hasRole } = useAuth();
  const canWrite = hasRole(ROLES.ADMIN, ROLES.ENGINEER);
  const devices = useDevices();
  const list = useList("/incidents", { status: "", severity: "", device_id: "", q: "" }, 15);
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(null);
  return (
    <>
      <PageHeader title="Incidents" subtitle="Track investigation status and operational history. Click a row for details.">
        {canWrite && <button className="btn" onClick={() => setOpen(true)} data-testid="add-incident-button"><Plus size={16} /> Open incident</button>}
      </PageHeader>
      <div className="toolbar">
        <input className="input search" placeholder="Search title or description" value={list.filters.q} onChange={(e) => list.update("q", e.target.value)} data-testid="incident-search-input" />
        <Select value={list.filters.status} onChange={(v) => list.update("status", v)} placeholder="All statuses" options={STATUSES} testid="incident-status-filter" />
        <Select value={list.filters.severity} onChange={(v) => list.update("severity", v)} placeholder="All severities" options={SEVERITIES} testid="incident-severity-filter" />
        <Select value={list.filters.device_id} onChange={(v) => list.update("device_id", v)} placeholder="All devices" options={devices.map((d) => [d.device_id, d.hostname])} testid="incident-device-filter" />
      </div>
      <ErrorBox error={list.error} />
      <DataTable rowKey="incident_id" rows={list.items} loading={list.loading} onRowClick={setSelected} testid="incidents-table" columns={[
        { key: "incident_id", label: "#", num: true },
        { key: "title", label: "Title", render: (i) => <strong>{i.title}</strong> },
        { key: "hostname", label: "Device" },
        { key: "severity", label: "Severity", render: (i) => <Pill value={i.severity} /> },
        { key: "status", label: "Status", render: (i) => <Pill value={i.status} /> },
        { key: "assignee", label: "Assignee", hideSm: true },
        { key: "opened_at", label: "Opened", hideSm: true, render: (i) => fmtDate(i.opened_at) },
      ]} />
      <Pager {...list} testid="incidents-pager" />
      <Modal open={open} title="Open incident" onClose={() => setOpen(false)} testid="incident-modal">
        <IncidentForm devices={devices} onClose={() => setOpen(false)} onSaved={() => { setOpen(false); list.reload(); }} />
      </Modal>
      <Modal open={!!selected} title={selected ? `Incident #${selected.incident_id}: ${selected.title}` : ""} onClose={() => setSelected(null)} wide testid="incident-detail-modal">
        {selected && <IncidentDetail id={selected.incident_id} canWrite={canWrite} onChanged={list.reload} />}
      </Modal>
    </>
  );
}
