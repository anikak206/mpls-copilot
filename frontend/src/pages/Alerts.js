import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { ROLES, useAuth } from "../context/AuthContext";
import { api, errMsg, fmtDate } from "../lib/api";
import { useDevices, useList } from "../lib/hooks";
import { DataTable, ErrorBox, Field, Modal, PageHeader, Pager, Pill, Select } from "../components/kit";

const SEVERITIES = ["info", "warning", "major", "critical"];

function AlertForm({ devices, onSaved, onClose }) {
  const [form, setForm] = useState({ device_id: "", severity: "warning", message: "" });
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    if (!form.device_id || form.message.trim().length < 3) return setError("Device and a message (min 3 characters) are required");
    try {
      await api.post("/alerts", { ...form, device_id: Number(form.device_id) });
      toast.success("Alert created");
      onSaved();
    } catch (err) {
      setError(errMsg(err));
    }
  };
  return (
    <form className="form-grid" onSubmit={submit} noValidate data-testid="alert-form">
      <div className="full"><ErrorBox error={error} testid="alert-form-error" /></div>
      <Field label="Device"><Select value={form.device_id} onChange={(v) => setForm({ ...form, device_id: v })} placeholder="Select device" options={devices.map((d) => [d.device_id, d.hostname])} testid="alert-device-select" /></Field>
      <Field label="Severity"><Select value={form.severity} onChange={(v) => setForm({ ...form, severity: v })} options={SEVERITIES} testid="alert-severity-select" /></Field>
      <Field label="Message" full><input className="input" maxLength={255} value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} data-testid="alert-message-input" /></Field>
      <div className="full btn-row"><button className="btn" type="submit" data-testid="alert-form-submit">Create alert</button><button className="btn ghost" type="button" onClick={onClose}>Cancel</button></div>
    </form>
  );
}

export default function Alerts() {
  const { hasRole } = useAuth();
  const canWrite = hasRole(ROLES.ADMIN, ROLES.ENGINEER);
  const devices = useDevices();
  const list = useList("/alerts", { status: "", severity: "", source: "", device_id: "", q: "" }, 15);
  const [open, setOpen] = useState(false);

  const act = async (alert, action) => {
    try {
      if (action === "escalate") {
        const { data } = await api.post(`/alerts/${alert.alert_id}/escalate`);
        toast.success(`Incident #${data.incident_id} opened via stored procedure`);
      } else {
        await api.patch(`/alerts/${alert.alert_id}`, { status: action });
        toast.success(`Alert ${action}`);
      }
      list.reload();
    } catch (e) {
      toast.error(errMsg(e));
    }
  };

  return (
    <>
      <PageHeader title="Alerts" subtitle="Raised by MySQL threshold triggers, the local ML model, or engineers.">
        {canWrite && <button className="btn" onClick={() => setOpen(true)} data-testid="add-alert-button"><Plus size={16} /> New alert</button>}
      </PageHeader>
      <div className="toolbar">
        <input className="input search" placeholder="Search message" value={list.filters.q} onChange={(e) => list.update("q", e.target.value)} data-testid="alert-search-input" />
        <Select value={list.filters.status} onChange={(v) => list.update("status", v)} placeholder="All statuses" options={["open", "acknowledged", "resolved"]} testid="alert-status-filter" />
        <Select value={list.filters.severity} onChange={(v) => list.update("severity", v)} placeholder="All severities" options={SEVERITIES} testid="alert-severity-filter" />
        <Select value={list.filters.source} onChange={(v) => list.update("source", v)} placeholder="All sources" options={["trigger", "ml", "manual"]} testid="alert-source-filter" />
        <Select value={list.filters.device_id} onChange={(v) => list.update("device_id", v)} placeholder="All devices" options={devices.map((d) => [d.device_id, d.hostname])} testid="alert-device-filter" />
      </div>
      <ErrorBox error={list.error} />
      <DataTable rowKey="alert_id" rows={list.items} loading={list.loading} testid="alerts-table" columns={[
        { key: "alert_id", label: "#", num: true },
        { key: "created_at", label: "Raised", render: (a) => fmtDate(a.created_at) },
        { key: "hostname", label: "Device", render: (a) => <strong>{a.hostname}</strong> },
        { key: "severity", label: "Severity", render: (a) => <Pill value={a.severity} /> },
        { key: "source", label: "Source", hideSm: true },
        { key: "message", label: "Message" },
        { key: "status", label: "Status", render: (a) => <Pill value={a.status} testid={`alert-status-${a.alert_id}`} /> },
        { key: "incident_id", label: "Incident", num: true, render: (a) => (a.incident_id ? `#${a.incident_id}` : "—") },
        { key: "ops", label: "", render: (a) => canWrite && (
          <div className="btn-row">
            {a.status === "open" && <button className="btn ghost sm" onClick={() => act(a, "acknowledged")} data-testid={`ack-alert-${a.alert_id}`}>Acknowledge</button>}
            {a.status !== "resolved" && <button className="btn ghost sm" onClick={() => act(a, "resolved")} data-testid={`resolve-alert-${a.alert_id}`}>Resolve</button>}
            {!a.incident_id && a.status !== "resolved" && <button className="btn sm" onClick={() => act(a, "escalate")} data-testid={`escalate-alert-${a.alert_id}`}>Escalate</button>}
          </div>
        ) },
      ]} />
      <Pager {...list} testid="alerts-pager" />
      <Modal open={open} title="New alert" onClose={() => setOpen(false)} testid="alert-modal">
        <AlertForm devices={devices} onClose={() => setOpen(false)} onSaved={() => { setOpen(false); list.reload(); }} />
      </Modal>
    </>
  );
}
