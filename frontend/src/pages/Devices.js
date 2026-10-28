import { useState } from "react";
import { Eye, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { ROLES, useAuth } from "../context/AuthContext";
import { api, errMsg, fmtDate } from "../lib/api";
import { useFetch, useList } from "../lib/hooks";
import { DataTable, ErrorBox, Field, Modal, PageHeader, Pager, Pill, Select } from "../components/kit";

import { validateDevice as validate } from "../lib/validation";

const TYPES = ["PE", "P", "CE", "RR"];
const STATUSES = ["up", "degraded", "down", "maintenance"];
const EMPTY = { hostname: "", mgmt_ip: "", device_type: "PE", vendor: "", model: "", site_id: "", status: "up", assigned_engineer_id: "" };

function DeviceForm({ initial, sites, engineers, onSaved, onClose }) {
  const [form, setForm] = useState({ ...EMPTY, ...initial });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const set = (k) => (v) => setForm({ ...form, [k]: v });
  const submit = async (e) => {
    e.preventDefault();
    const errs = validate(form);
    setErrors(errs);
    if (Object.keys(errs).length) return;
    const body = { ...form, site_id: Number(form.site_id), assigned_engineer_id: form.assigned_engineer_id ? Number(form.assigned_engineer_id) : null };
    ["device_id", "site_name", "region", "assigned_engineer", "created_at", "updated_at"].forEach((k) => delete body[k]);
    try {
      if (initial.device_id) await api.patch(`/devices/${initial.device_id}`, body);
      else await api.post("/devices", body);
      toast.success(initial.device_id ? "Device updated" : "Device created");
      onSaved();
    } catch (err) {
      setError(errMsg(err));
    }
  };
  return (
    <form onSubmit={submit} noValidate className="form-grid" data-testid="device-form">
      <div className="full"><ErrorBox error={error} testid="device-form-error" /></div>
      <Field label="Hostname" error={errors.hostname}><input className="input" value={form.hostname} onChange={(e) => set("hostname")(e.target.value)} data-testid="device-hostname-input" /></Field>
      <Field label="Management IP" error={errors.mgmt_ip}><input className="input" value={form.mgmt_ip} onChange={(e) => set("mgmt_ip")(e.target.value)} data-testid="device-ip-input" /></Field>
      <Field label="Type"><Select value={form.device_type} onChange={set("device_type")} options={TYPES} testid="device-type-select" /></Field>
      <Field label="Status"><Select value={form.status} onChange={set("status")} options={STATUSES} testid="device-status-select" /></Field>
      <Field label="Vendor" error={errors.vendor}><input className="input" value={form.vendor} onChange={(e) => set("vendor")(e.target.value)} data-testid="device-vendor-input" /></Field>
      <Field label="Model" error={errors.model}><input className="input" value={form.model} onChange={(e) => set("model")(e.target.value)} data-testid="device-model-input" /></Field>
      <Field label="Site" error={errors.site_id}><Select value={form.site_id} onChange={set("site_id")} placeholder="Select site" options={sites.map((s) => [s.site_id, s.name])} testid="device-site-select" /></Field>
      <Field label="Assigned engineer"><Select value={form.assigned_engineer_id || ""} onChange={set("assigned_engineer_id")} placeholder="Unassigned" options={engineers.map((u) => [u.user_id, u.full_name])} testid="device-engineer-select" /></Field>
      <div className="full btn-row"><button className="btn" type="submit" data-testid="device-form-submit">Save device</button><button type="button" className="btn ghost" onClick={onClose}>Cancel</button></div>
    </form>
  );
}

function DeviceDetail({ id }) {
  const { data, error } = useFetch(`/devices/${id}`);
  if (error) return <ErrorBox error={error} />;
  if (!data) return <div className="empty">Loading…</div>;
  const p = data.latest_prediction;
  return (
    <div data-testid="device-detail">
      <dl className="kv">
        {[["Hostname", data.hostname], ["IP", data.mgmt_ip], ["Type", data.device_type], ["Vendor / model", `${data.vendor} ${data.model}`], ["Site", `${data.site_name} (${data.region})`], ["Engineer", data.assigned_engineer || "Unassigned"], ["Open alerts", data.open_alerts], ["Updated", fmtDate(data.updated_at)]].map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}
        <div><dt>Status</dt><dd><Pill value={data.status} /></dd></div>
        <div><dt>Latest risk</dt><dd>{p ? <><Pill value={p.label} /> <span className="mono">{p.risk_score}</span></> : "—"}</dd></div>
      </dl>
      <h3 className="section-title" style={{ marginTop: 18 }}>Recent telemetry</h3>
      <DataTable rowKey="telemetry_id" rows={data.recent_telemetry.slice(0, 10)} testid="device-telemetry-table" columns={[
        { key: "recorded_at", label: "Time", render: (r) => fmtDate(r.recorded_at) },
        { key: "cpu_util", label: "CPU %", num: true }, { key: "latency_ms", label: "Latency", num: true },
        { key: "packet_loss_pct", label: "Loss %", num: true }, { key: "lsp_flaps", label: "LSP flaps", num: true },
      ]} />
    </div>
  );
}

export default function Devices() {
  const { hasRole } = useAuth();
  const isAdmin = hasRole(ROLES.ADMIN);
  const list = useList("/devices", { q: "", status: "", device_type: "", site_id: "" }, 10);
  const sites = useFetch("/sites").data || [];
  const engineers = useFetch(isAdmin ? "/users/engineers" : "/sites").data || [];
  const [editing, setEditing] = useState(null);
  const [viewing, setViewing] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const remove = async () => {
    try {
      await api.delete(`/devices/${deleting.device_id}`);
      toast.success("Device deleted");
      setDeleting(null);
      list.reload();
    } catch (e) {
      toast.error(errMsg(e));
    }
  };

  return (
    <>
      <PageHeader title="Devices" subtitle="MPLS PE, P, CE and route-reflector inventory.">
        {isAdmin && <button className="btn" onClick={() => setEditing({})} data-testid="add-device-button"><Plus size={16} /> Add device</button>}
      </PageHeader>
      <div className="toolbar">
        <input className="input search" placeholder="Search hostname, IP, vendor, model" value={list.filters.q} onChange={(e) => list.update("q", e.target.value)} data-testid="device-search-input" />
        <Select value={list.filters.status} onChange={(v) => list.update("status", v)} placeholder="All statuses" options={STATUSES} testid="device-status-filter" />
        <Select value={list.filters.device_type} onChange={(v) => list.update("device_type", v)} placeholder="All types" options={TYPES} testid="device-type-filter" />
        <Select value={list.filters.site_id} onChange={(v) => list.update("site_id", v)} placeholder="All sites" options={sites.map((s) => [s.site_id, s.name])} testid="device-site-filter" />
      </div>
      <ErrorBox error={list.error} />
      <DataTable rowKey="device_id" rows={list.items} loading={list.loading} testid="devices-table" columns={[
        { key: "hostname", label: "Hostname", render: (d) => <strong>{d.hostname}</strong> },
        { key: "mgmt_ip", label: "Mgmt IP", num: true },
        { key: "device_type", label: "Type" },
        { key: "vendor", label: "Vendor / model", hideSm: true, render: (d) => `${d.vendor} ${d.model}` },
        { key: "site_name", label: "Site", hideSm: true },
        { key: "assigned_engineer", label: "Engineer", hideSm: true },
        { key: "status", label: "Status", render: (d) => <Pill value={d.status} /> },
        { key: "actions", label: "", render: (d) => (
          <div className="btn-row">
            <button className="btn ghost sm" onClick={() => setViewing(d)} data-testid={`view-device-${d.device_id}`}><Eye size={13} /> View</button>
            {isAdmin && <button className="btn ghost sm" onClick={() => setEditing(d)} data-testid={`edit-device-${d.device_id}`}><Pencil size={13} /></button>}
            {isAdmin && <button className="btn danger sm" onClick={() => setDeleting(d)} data-testid={`delete-device-${d.device_id}`}><Trash2 size={13} /></button>}
          </div>
        ) },
      ]} />
      <Pager {...list} testid="devices-pager" />
      <Modal open={!!editing} title={editing?.device_id ? `Edit ${editing.hostname}` : "Add device"} onClose={() => setEditing(null)} testid="device-modal">
        {editing && <DeviceForm initial={editing} sites={sites} engineers={engineers} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); list.reload(); }} />}
      </Modal>
      <Modal open={!!viewing} title={viewing?.hostname || ""} onClose={() => setViewing(null)} wide testid="device-detail-modal">
        {viewing && <DeviceDetail id={viewing.device_id} />}
      </Modal>
      <Modal open={!!deleting} title="Delete device" onClose={() => setDeleting(null)} testid="delete-device-modal">
        <p>Delete <strong>{deleting?.hostname}</strong>? Its telemetry, predictions, alerts, incidents and actions are removed too (cascade). This is recorded in the audit log.</p>
        <div className="btn-row"><button className="btn danger" onClick={remove} data-testid="confirm-delete-device">Delete</button><button className="btn ghost" onClick={() => setDeleting(null)}>Cancel</button></div>
      </Modal>
    </>
  );
}
