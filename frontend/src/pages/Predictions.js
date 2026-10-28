import { useState } from "react";
import { BrainCircuit, Info } from "lucide-react";
import { toast } from "sonner";
import { ROLES, useAuth } from "../context/AuthContext";
import { api, errMsg, fmtDate } from "../lib/api";
import { useDevices, useFetch, useList } from "../lib/hooks";
import { DataTable, ErrorBox, Field, Modal, PageHeader, Pager, Pill, Select } from "../components/kit";
import { FEATURE_DEFAULTS, FeatureInputs, validateFeatures } from "./Telemetry";

export function PredictionResult({ p }) {
  return (
    <div className={`result-card ${p.label}`} data-testid="prediction-result">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
        <div className="btn-row" style={{ alignItems: "center" }}>
          <Pill value={p.label} testid="prediction-result-label" /> <Pill value={p.risk_level} /> <Pill value={p.mode} />
          <span className="small muted">{p.hostname} · #{p.prediction_id} · {fmtDate(p.created_at)}</span>
        </div>
        <div><span className="risk-big" data-testid="prediction-result-risk">{p.risk_score}</span><span className="muted"> /100</span></div>
      </div>
      <div className="meter"><span style={{ width: `${p.risk_score}%` }} /></div>
      <p style={{ margin: 0 }} data-testid="prediction-result-explanation">{p.explanation}</p>
      {p.recommendation && (
        <div className="card" data-testid="prediction-result-recommendation">
          <div className="btn-row" style={{ alignItems: "center" }}><strong>{p.recommendation.title}</strong> <Pill value={p.recommendation.priority} /> <span className="mono small muted">{p.recommendation.action_code}</span></div>
          <p className="small" style={{ margin: "6px 0 0" }}>{p.recommendation.rationale}</p>
        </div>
      )}
    </div>
  );
}

function RunPanel({ devices, onDone }) {
  const [mode, setMode] = useState("features");
  const [deviceId, setDeviceId] = useState("");
  const [telemetryId, setTelemetryId] = useState("");
  const [values, setValues] = useState(FEATURE_DEFAULTS);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const run = async (e) => {
    e.preventDefault();
    let body;
    if (mode === "telemetry") {
      if (!Number(telemetryId)) return setErrors({ telemetry: "Enter a telemetry sample ID" });
      body = { telemetry_id: Number(telemetryId) };
    } else {
      const errs = validateFeatures(values);
      if (!deviceId) errs.device = "Select a device";
      setErrors(errs);
      if (Object.keys(errs).length) return;
      body = { device_id: Number(deviceId), features: Object.fromEntries(Object.entries(values).map(([k, v]) => [k, Number(v)])) };
    }
    setErrors({});
    setBusy(true);
    try {
      const { data } = await api.post("/predictions/run", body);
      setResult(data);
      setError("");
      toast.success(`Prediction #${data.prediction_id} saved`);
      onDone();
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <form className="card" onSubmit={run} noValidate data-testid="prediction-run-form" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <h3 className="section-title" style={{ margin: 0 }}><BrainCircuit size={16} /> Run local prediction</h3>
      <div className="btn-row">
        <button type="button" className={`btn sm ${mode === "features" ? "" : "ghost"}`} onClick={() => setMode("features")} data-testid="predict-mode-features">Enter features</button>
        <button type="button" className={`btn sm ${mode === "telemetry" ? "" : "ghost"}`} onClick={() => setMode("telemetry")} data-testid="predict-mode-telemetry">Existing telemetry sample</button>
      </div>
      <ErrorBox error={error} testid="prediction-run-error" />
      {mode === "telemetry" ? (
        <Field label="Telemetry ID" error={errors.telemetry}><input className="input" type="number" min="1" value={telemetryId} onChange={(e) => setTelemetryId(e.target.value)} data-testid="predict-telemetry-id-input" /></Field>
      ) : (
        <div className="form-grid">
          <Field label="Device" error={errors.device} full><Select value={deviceId} onChange={setDeviceId} placeholder="Select device" options={devices.map((d) => [d.device_id, d.hostname])} testid="predict-device-select" /></Field>
          <FeatureInputs values={values} setValues={setValues} errors={errors} prefix="predict" />
        </div>
      )}
      <div className="btn-row"><button className="btn" type="submit" disabled={busy} data-testid="predict-run-button">{busy ? "Scoring…" : "Run prediction"}</button></div>
      {result && <PredictionResult p={result} />}
    </form>
  );
}

function ModelInfo() {
  const { data } = useFetch("/ml/model-info");
  if (!data) return null;
  const m = data.metrics;
  return (
    <div className="card aqua" data-testid="model-info">
      <h3 className="section-title"><Info size={16} /> Model · <span className="mono">{data.model_version}</span> <Pill value={data.mode} /></h3>
      <p className="small" style={{ margin: "0 0 8px" }}>{data.metadata.algorithm}. {data.runtime}</p>
      {m && <p className="small mono" style={{ margin: "0 0 8px" }}>Held-out synthetic set: ROC-AUC {m.roc_auc} · precision {m.anomalous_threshold_60.precision} · recall {m.anomalous_threshold_60.recall} · F1 {m.anomalous_threshold_60.f1}</p>}
      <p className="small" style={{ margin: "0 0 4px" }}><strong>Labels:</strong> {data.metadata.label_rule}</p>
      <ul className="small" style={{ margin: 0, paddingLeft: 18 }}>{(data.metadata.limitations || []).map((l) => <li key={l}>{l}</li>)}</ul>
    </div>
  );
}

export default function Predictions() {
  const { hasRole } = useAuth();
  const canRun = hasRole(ROLES.ADMIN, ROLES.ENGINEER);
  const devices = useDevices();
  const list = useList("/predictions", { label: "", risk_level: "", device_id: "" }, 12);
  const [selected, setSelected] = useState(null);
  return (
    <>
      <PageHeader title="Predictions" subtitle="Local anomaly detection with explainable, calibrated risk scores." />
      <div className="grid grid-2" style={{ marginBottom: 20, alignItems: "start" }}>
        {canRun ? <RunPanel devices={devices} onDone={list.reload} /> : <div className="card note-box">Auditors can review predictions but cannot run the model.</div>}
        <ModelInfo />
      </div>
      <div className="toolbar">
        <Select value={list.filters.label} onChange={(v) => list.update("label", v)} placeholder="All results" options={["normal", "uncertain", "anomalous"]} testid="prediction-label-filter" />
        <Select value={list.filters.risk_level} onChange={(v) => list.update("risk_level", v)} placeholder="All risk levels" options={["low", "medium", "high", "critical"]} testid="prediction-level-filter" />
        <Select value={list.filters.device_id} onChange={(v) => list.update("device_id", v)} placeholder="All devices" options={devices.map((d) => [d.device_id, d.hostname])} testid="prediction-device-filter" />
      </div>
      <ErrorBox error={list.error} />
      <DataTable rowKey="prediction_id" rows={list.items} loading={list.loading} onRowClick={setSelected} testid="predictions-table" columns={[
        { key: "prediction_id", label: "#", num: true },
        { key: "created_at", label: "Time", render: (p) => fmtDate(p.created_at) },
        { key: "hostname", label: "Device", render: (p) => <strong>{p.hostname}</strong> },
        { key: "label", label: "Result", render: (p) => <Pill value={p.label} /> },
        { key: "risk_score", label: "Risk", num: true },
        { key: "risk_level", label: "Level", render: (p) => <Pill value={p.risk_level} /> },
        { key: "rec", label: "Recommendation", hideSm: true, render: (p) => p.recommendation?.title },
        { key: "mode", label: "Mode", hideSm: true, render: (p) => <Pill value={p.mode} /> },
      ]} />
      <Pager {...list} testid="predictions-pager" />
      <Modal open={!!selected} title={selected ? `Prediction #${selected.prediction_id}` : ""} onClose={() => setSelected(null)} wide testid="prediction-detail-modal">
        {selected && <><PredictionResult p={selected} /><dl className="kv">{Object.entries(selected.features).map(([k, v]) => <div key={k}><dt>{k}</dt><dd className="mono">{v}</dd></div>)}</dl></>}
      </Modal>
    </>
  );
}
