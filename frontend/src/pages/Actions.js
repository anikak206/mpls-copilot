import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { ROLES, useAuth } from "../context/AuthContext";
import { api, errMsg, fmtDate } from "../lib/api";
import { useDevices, useList } from "../lib/hooks";
import { DataTable, ErrorBox, Field, Modal, PageHeader, Pager, Pill, Select } from "../components/kit";

const TYPES = ["config_change", "interface_reset", "traffic_reroute", "hardware_check", "escalation", "monitoring", "other"];
const RESULTS = ["resolved", "improved", "no_change", "worsened"];

function OutcomeFields({ value, onChange, prefix, required }) {
  return (
    <>
      <Field label="Outcome result"><Select value={value.result} onChange={(v) => onChange({ ...value, result: v })} placeholder={required ? undefined : "Not yet known"} options={RESULTS} testid={`${prefix}-outcome-result-select`} /></Field>
      <Field label="Outcome notes" full><textarea className="textarea" rows={2} value={value.notes} onChange={(e) => onChange({ ...value, notes: e.target.value })} data-testid={`${prefix}-outcome-notes-input`} /></Field>
    </>
  );
}

export function ActionForm({ preset = {}, onSaved, onClose }) {
  const devices = useDevices();
  const [form, setForm] = useState({ device_id: "", recommendation_id: "", incident_id: "", action_type: "monitoring", description: "", ...preset });
  const [outcome, setOutcome] = useState({ result: "", notes: "" });
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    if (!form.device_id || form.description.trim().length < 3) return setError("Device and a description (min 3 characters) are required");
    if (outcome.result && outcome.notes.trim().length < 3) return setError("Add outcome notes (min 3 characters) or clear the outcome");
    const num = (v) => (v ? Number(v) : null);
    try {
      await api.post("/actions", { device_id: Number(form.device_id), recommendation_id: num(form.recommendation_id), incident_id: num(form.incident_id), action_type: form.action_type, description: form.description, outcome: outcome.result ? outcome : null });
      toast.success("Action recorded");
      onSaved();
    } catch (err) {
      setError(errMsg(err));
    }
  };
  return (
    <form className="form-grid" onSubmit={submit} noValidate data-testid="action-form">
      <div className="full"><ErrorBox error={error} testid="action-form-error" /></div>
      <Field label="Device"><Select value={form.device_id} onChange={(v) => setForm({ ...form, device_id: v })} placeholder="Select device" options={devices.map((d) => [d.device_id, d.hostname])} testid="action-device-select" /></Field>
      <Field label="Action type"><Select value={form.action_type} onChange={(v) => setForm({ ...form, action_type: v })} options={TYPES} testid="action-type-select" /></Field>
      <Field label="Recommendation ID (optional)"><input className="input" type="number" min="1" value={form.recommendation_id} onChange={(e) => setForm({ ...form, recommendation_id: e.target.value })} data-testid="action-recommendation-input" /></Field>
      <Field label="Incident ID (optional)"><input className="input" type="number" min="1" value={form.incident_id} onChange={(e) => setForm({ ...form, incident_id: e.target.value })} data-testid="action-incident-input" /></Field>
      <Field label="What was done" full><textarea className="textarea" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} data-testid="action-description-input" /></Field>
      <OutcomeFields value={outcome} onChange={setOutcome} prefix="action" />
      <div className="full btn-row"><button className="btn" type="submit" data-testid="action-form-submit">Save action</button><button className="btn ghost" type="button" onClick={onClose}>Cancel</button></div>
    </form>
  );
}

function OutcomeForm({ action, onSaved }) {
  const [value, setValue] = useState({ result: "improved", notes: "" });
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    if (value.notes.trim().length < 3) return setError("Notes are required (min 3 characters)");
    try {
      await api.post(`/actions/${action.action_id}/outcome`, value);
      toast.success("Outcome recorded");
      onSaved();
    } catch (err) {
      setError(errMsg(err));
    }
  };
  return (
    <form className="form-grid" onSubmit={submit} noValidate data-testid="outcome-form">
      <div className="full"><ErrorBox error={error} testid="outcome-form-error" /></div>
      <OutcomeFields value={value} onChange={setValue} prefix="outcome" required />
      <div className="full"><button className="btn" type="submit" data-testid="outcome-form-submit">Save outcome</button></div>
    </form>
  );
}

export default function Actions() {
  const { hasRole } = useAuth();
  const canWrite = hasRole(ROLES.ADMIN, ROLES.ENGINEER);
  const devices = useDevices();
  const list = useList("/actions", { device_id: "", action_type: "", has_outcome: "" }, 12);
  const [open, setOpen] = useState(false);
  const [outcomeFor, setOutcomeFor] = useState(null);
  return (
    <>
      <PageHeader title="Engineer actions & outcomes" subtitle="What was done, linked to device, recommendation and incident, and how it turned out.">
        {canWrite && <button className="btn" onClick={() => setOpen(true)} data-testid="add-action-button"><Plus size={16} /> Record action</button>}
      </PageHeader>
      <div className="toolbar">
        <Select value={list.filters.device_id} onChange={(v) => list.update("device_id", v)} placeholder="All devices" options={devices.map((d) => [d.device_id, d.hostname])} testid="action-device-filter" />
        <Select value={list.filters.action_type} onChange={(v) => list.update("action_type", v)} placeholder="All action types" options={TYPES} testid="action-type-filter" />
        <Select value={list.filters.has_outcome} onChange={(v) => list.update("has_outcome", v)} placeholder="Any outcome state" options={[["true", "With outcome"], ["false", "Awaiting outcome"]]} testid="action-outcome-filter" />
      </div>
      <ErrorBox error={list.error} />
      <DataTable rowKey="action_id" rows={list.items} loading={list.loading} testid="actions-table" columns={[
        { key: "action_id", label: "#", num: true },
        { key: "performed_at", label: "When", render: (a) => fmtDate(a.performed_at) },
        { key: "hostname", label: "Device", render: (a) => <strong>{a.hostname}</strong> },
        { key: "action_type", label: "Type", render: (a) => a.action_type.replace(/_/g, " ") },
        { key: "description", label: "Description" },
        { key: "links", label: "Links", hideSm: true, render: (a) => <span className="mono small">{a.recommendation_id ? `rec #${a.recommendation_id} ` : ""}{a.incident_id ? `inc #${a.incident_id}` : ""}</span> },
        { key: "engineer", label: "Engineer", hideSm: true },
        { key: "outcome", label: "Outcome", render: (a) => a.outcome ? <span title={a.outcome.notes}><Pill value={a.outcome.result} /></span> : canWrite ? <button className="btn ghost sm" onClick={() => setOutcomeFor(a)} data-testid={`add-outcome-${a.action_id}`}>Add outcome</button> : "—" },
      ]} />
      <Pager {...list} testid="actions-pager" />
      <Modal open={open} title="Record engineer action" onClose={() => setOpen(false)} testid="action-modal">
        <ActionForm onClose={() => setOpen(false)} onSaved={() => { setOpen(false); list.reload(); }} />
      </Modal>
      <Modal open={!!outcomeFor} title={`Outcome for action #${outcomeFor?.action_id}`} onClose={() => setOutcomeFor(null)} testid="outcome-modal">
        {outcomeFor && <OutcomeForm action={outcomeFor} onSaved={() => { setOutcomeFor(null); list.reload(); }} />}
      </Modal>
    </>
  );
}
