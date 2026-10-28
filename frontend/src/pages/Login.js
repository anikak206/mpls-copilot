import { useState } from "react";
import { BrainCircuit, Database, Lock, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { errMsg } from "../lib/api";
import { ErrorBox, Field } from "../components/kit";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Login() {
  const { login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    const next = {};
    if (!EMAIL_RE.test(form.email.trim())) next.email = "Enter a valid email address";
    if (!form.password) next.password = "Password is required";
    setErrors(next);
    if (Object.keys(next).length) return;
    setBusy(true);
    setError("");
    try {
      await login(form.email.trim(), form.password);
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login">
      <section className="login-art">
        <div className="brand">
          <div className="brand-mark"><ShieldCheck size={20} /></div>
          <div><div className="brand-title">MPLS Copilot</div><div className="brand-sub">Secure operations</div></div>
        </div>
        <div>
          <h1>Air-Gapped Predictive Copilot for Secure MPLS Operations</h1>
          <p>Monitor devices, telemetry, alerts and incidents. Local machine learning flags abnormal behaviour and suggests preventive action, with no data leaving your network.</p>
        </div>
        <ul className="feature-list">
          <li><BrainCircuit size={18} /> On-premise anomaly detection with explainable risk scores</li>
          <li><Database size={18} /> MySQL-backed records with full audit trail</li>
          <li><Lock size={18} /> Role-based access for Administrators, Engineers and Auditors</li>
        </ul>
      </section>
      <section className="login-form">
        <form onSubmit={submit} noValidate data-testid="login-form">
          <div>
            <h2 style={{ fontSize: 24, margin: 0 }}>Sign in</h2>
            <p className="muted" style={{ margin: "4px 0 0" }}>Use your organisation account.</p>
          </div>
          <ErrorBox error={error} testid="login-error" />
          <Field label="Email" error={errors.email}>
            <input className="input" type="email" autoComplete="username" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} data-testid="login-email-input" />
          </Field>
          <Field label="Password" error={errors.password}>
            <input className="input" type="password" autoComplete="current-password" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })} data-testid="login-password-input" />
          </Field>
          <button className="btn" type="submit" disabled={busy} style={{ justifyContent: "center" }} data-testid="login-submit-button">
            {busy ? "Signing in…" : "Sign in"}
          </button>
          <p className="small muted">Sessions expire automatically. Repeated failed attempts are temporarily locked.</p>
        </form>
      </section>
    </div>
  );
}
