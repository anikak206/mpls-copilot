import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { ROLES, useAuth } from "../context/AuthContext";
import { api, errMsg, fmtDate } from "../lib/api";
import { useDevices, useList } from "../lib/hooks";
import { DataTable, ErrorBox, Field, Modal, PageHeader, Pager, Select } from "../components/kit";

import { FEATURE_DEFAULTS, FEATURE_FIELDS, validateFeatures } from "../lib/validation";

export { FEATURE_DEFAULTS, validateFeatures };

export function FeatureInputs({ values, setValues, errors, prefix = "tel" }) {
  return FEATURE_FIELDS.map(([k, label, min, max, step]) => (
    <Field key={k} label={label} error={errors[k]}>
      <input className="input" type="number" min={min} max={max} step={step} value={values[k]}
        onChange={(e) => setValues({ ...values, [k]: e.target.value })} data-testid={`${prefix}-${k}-input`} />
    </Field>
  ));
}

function TelemetryForm({ devices, onSaved, onClose }) {
  const [deviceId, setDeviceId] = useState("");
  const [values, setValues] = useState(FEATURE_DEFAULTS);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    const errs = validateFeatures(values);
    if (!deviceId) errs.device = "Select a device";
    setErrors(errs);
    if (Object.keys(errs).length) return;
    try {
      const body = { device_id: Number(deviceId), ...Object.fromEntries(Object.entries(values).map(([k, v]) => [k, Number(v)])) };
      const { data } = await api.post("/telemetry", body);
      toast.success(data.trigger_alerts.length ? `Sample saved · trigger raised ${data.trigger_alerts.length} alert(s)` : "Sample saved");
      onSaved();
    } catch (err) {
      setError(errMsg(err));
    }
  };
  return (
    <form className="form-grid" onSubmit={submit} noValidate data-testid="telemetry-form">
      <div className="full"><ErrorBox error={error} testid="telemetry-form-error" /></div>
      <Field label="Device" error={errors.device} full><Select value={deviceId} onChange={setDeviceId} placeholder="Select device" options={devices.map((d) => [d.device_id, d.hostname])} testid="telemetry-device-select" /></Field>
      <FeatureInputs values={values} setValues={setValues} errors={errors} />
      <div className="full note-box small">Samples breaching hard thresholds (loss ≥ 2%, CPU ≥ 85%, latency ≥ 150 ms, LSP flaps ≥ 5) raise an alert automatically via a MySQL trigger.</div>
      <div className="full btn-row"><button className="btn" type="submit" data-testid="telemetry-form-submit">Save sample</button><button className="btn ghost" type="button" onClick={onClose}>Cancel</button></div>
    </form>
  );
}

export default function Telemetry() {
  const { hasRole } = useAuth();
  const canWrite = hasRole(ROLES.ADMIN, ROLES.ENGINEER);
  const devices = useDevices();
  const list = useList("/telemetry", { device_id: "", source: "", date_from: "", date_to: "", min_loss: "" }, 20);
  const [open, setOpen] = useState(false);
  return (
    <>
      <PageHeader title="Telemetry" subtitle="Performance samples per device. Times shown in your local timezone.">
        {canWrite && <button className="btn" onClick={() => setOpen(true)} data-testid="add-telemetry-button"><Plus size={16} /> Record telemetry</button>}
      </PageHeader>
      <div className="toolbar">
        <Select value={list.filters.device_id} onChange={(v) => list.update("device_id", v)} placeholder="All devices" options={devices.map((d) => [d.device_id, d.hostname])} testid="telemetry-device-filter" />
        <Select value={list.filters.source} onChange={(v) => list.update("source", v)} placeholder="All sources" options={["manual", "collector", "seed"]} testid="telemetry-source-filter" />
        <Field label="From"><input className="input" type="datetime-local" value={list.filters.date_from} onChange={(e) => list.update("date_from", e.target.value)} data-testid="telemetry-from-filter" /></Field>
        <Field label="To"><input className="input" type="datetime-local" value={list.filters.date_to} onChange={(e) => list.update("date_to", e.target.value)} data-testid="telemetry-to-filter" /></Field>
        <Field label="Min loss %"><input className="input" type="number" min="0" step="0.1" value={list.filters.min_loss} onChange={(e) => list.update("min_loss", e.target.value)} data-testid="telemetry-loss-filter" /></Field>
      </div>
      <ErrorBox error={list.error} />
      <DataTable rowKey="telemetry_id" rows={list.items} loading={list.loading} testid="telemetry-table" columns={[
        { key: "telemetry_id", label: "#", num: true },
        { key: "recorded_at", label: "Recorded", render: (r) => fmtDate(r.recorded_at) },
        { key: "hostname", label: "Device", render: (r) => <strong>{r.hostname}</strong> },
        { key: "cpu_util", label: "CPU %", num: true }, { key: "mem_util", label: "Mem %", num: true, hideSm: true },
        { key: "latency_ms", label: "Latency ms", num: true }, { key: "jitter_ms", label: "Jitter", num: true, hideSm: true },
        { key: "packet_loss_pct", label: "Loss %", num: true }, { key: "throughput_mbps", label: "Mbps", num: true, hideSm: true },
        { key: "crc_errors", label: "CRC", num: true, hideSm: true }, { key: "lsp_flaps", label: "LSP", num: true, hideSm: true },
        { key: "bgp_flaps", label: "BGP", num: true, hideSm: true }, { key: "source", label: "Source" },
      ]} />
      <Pager {...list} testid="telemetry-pager" />
      <Modal open={open} title="Record telemetry sample" onClose={() => setOpen(false)} testid="telemetry-modal">
        <TelemetryForm devices={devices} onClose={() => setOpen(false)} onSaved={() => { setOpen(false); list.reload(); }} />
      </Modal>
    </>
  );
}
