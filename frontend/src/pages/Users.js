import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { api, errMsg, fmtDate } from "../lib/api";
import { useFetch, useList } from "../lib/hooks";
import { DataTable, ErrorBox, Field, Modal, PageHeader, Pager, Select } from "../components/kit";

const ROLE_NAMES = ["Administrator", "Network Engineer", "Auditor"];
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function UserForm({ initial, onSaved, onClose }) {
  const editing = Boolean(initial.user_id);
  const [form, setForm] = useState({ email: initial.email || "", full_name: initial.full_name || "", role: initial.role || "Network Engineer", password: "", is_active: initial.is_active ?? true });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!editing && !EMAIL_RE.test(form.email)) errs.email = "Enter a valid email";
    if (form.full_name.trim().length < 2) errs.full_name = "Name is required";
    if ((!editing || form.password) && form.password.length < 10) errs.password = "At least 10 characters";
    setErrors(errs);
    if (Object.keys(errs).length) return;
    try {
      if (editing) {
        const body = { full_name: form.full_name, role: form.role, is_active: form.is_active };
        if (form.password) body.password = form.password;
        await api.patch(`/users/${initial.user_id}`, body);
      } else {
        await api.post("/users", { email: form.email, full_name: form.full_name, role: form.role, password: form.password });
      }
      toast.success(editing ? "User updated" : "User created");
      onSaved();
    } catch (err) {
      setError(errMsg(err));
    }
  };
  return (
    <form className="form-grid" onSubmit={submit} noValidate data-testid="user-form">
      <div className="full"><ErrorBox error={error} testid="user-form-error" /></div>
      <Field label="Email" error={errors.email}><input className="input" type="email" disabled={editing} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} data-testid="user-email-input" /></Field>
      <Field label="Full name" error={errors.full_name}><input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} data-testid="user-name-input" /></Field>
      <Field label="Role"><Select value={form.role} onChange={(v) => setForm({ ...form, role: v })} options={ROLE_NAMES} testid="user-role-select" /></Field>
      <Field label={editing ? "New password (optional)" : "Password"} error={errors.password}><input className="input" type="password" autoComplete="new-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} data-testid="user-password-input" /></Field>
      {editing && <Field label="Account status"><Select value={String(form.is_active)} onChange={(v) => setForm({ ...form, is_active: v === "true" })} options={[["true", "Active"], ["false", "Disabled"]]} testid="user-active-select" /></Field>}
      <div className="full btn-row"><button className="btn" type="submit" data-testid="user-form-submit">Save user</button><button className="btn ghost" type="button" onClick={onClose}>Cancel</button></div>
    </form>
  );
}

export default function UsersPage() {
  const { user: me } = useAuth();
  const list = useList("/users", { q: "", role: "", is_active: "" }, 15);
  const roles = useFetch("/roles").data || [];
  const [editing, setEditing] = useState(null);
  const deactivate = async (u) => {
    if (!window.confirm(`Deactivate ${u.email}? They will no longer be able to sign in.`)) return;
    try {
      await api.delete(`/users/${u.user_id}`);
      toast.success("User deactivated");
      list.reload();
    } catch (e) {
      toast.error(errMsg(e));
    }
  };
  return (
    <>
      <PageHeader title="Users & roles" subtitle="All accounts live in one users table; permissions come from the assigned role.">
        <button className="btn" onClick={() => setEditing({})} data-testid="add-user-button"><Plus size={16} /> Add user</button>
      </PageHeader>
      <div className="grid grid-3" style={{ marginBottom: 16 }}>
        {roles.map((r) => <div className="stat" key={r.role_id} data-testid={`role-card-${r.role_id}`}><span className="stat-label">{r.name}</span><span className="small">{r.description}</span></div>)}
      </div>
      <div className="toolbar">
        <input className="input search" placeholder="Search name or email" value={list.filters.q} onChange={(e) => list.update("q", e.target.value)} data-testid="user-search-input" />
        <Select value={list.filters.role} onChange={(v) => list.update("role", v)} placeholder="All roles" options={ROLE_NAMES} testid="user-role-filter" />
        <Select value={list.filters.is_active} onChange={(v) => list.update("is_active", v)} placeholder="Any status" options={[["true", "Active"], ["false", "Disabled"]]} testid="user-active-filter" />
      </div>
      <ErrorBox error={list.error} />
      <DataTable rowKey="user_id" rows={list.items} loading={list.loading} testid="users-table" columns={[
        { key: "full_name", label: "Name", render: (u) => <strong>{u.full_name}</strong> },
        { key: "email", label: "Email" },
        { key: "role", label: "Role", render: (u) => <span className="pill pill-role">{u.role}</span> },
        { key: "is_active", label: "Status", render: (u) => <span className={`pill ${u.is_active ? "pill-up" : "pill-down"}`}>{u.is_active ? "Active" : "Disabled"}</span> },
        { key: "last_login_at", label: "Last login", hideSm: true, render: (u) => fmtDate(u.last_login_at) },
        { key: "ops", label: "", render: (u) => (
          <div className="btn-row">
            <button className="btn ghost sm" onClick={() => setEditing(u)} data-testid={`edit-user-${u.user_id}`}>Edit</button>
            {u.is_active && u.user_id !== me.user_id && <button className="btn danger sm" onClick={() => deactivate(u)} data-testid={`deactivate-user-${u.user_id}`}>Deactivate</button>}
          </div>
        ) },
      ]} />
      <Pager {...list} testid="users-pager" />
      <Modal open={!!editing} title={editing?.user_id ? `Edit ${editing.full_name}` : "Add user"} onClose={() => setEditing(null)} testid="user-modal">
        {editing && <UserForm initial={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); list.reload(); }} />}
      </Modal>
    </>
  );
}
