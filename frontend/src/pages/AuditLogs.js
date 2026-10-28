import { Download, Lock } from "lucide-react";
import { toast } from "sonner";
import { downloadFile, errMsg, fmtDate } from "../lib/api";
import { useFetch, useList } from "../lib/hooks";
import { DataTable, ErrorBox, Field, PageHeader, Pager, Select } from "../components/kit";

export default function AuditLogs() {
  const list = useList("/audit-logs", { action: "", entity_type: "", date_from: "", date_to: "" }, 20);
  const actions = useFetch("/audit-logs/actions").data || [];
  const exportCsv = async () => {
    try {
      await downloadFile("/audit-logs/export", list.filters, "audit_logs.csv");
      toast.success("Audit CSV downloaded");
    } catch (e) {
      toast.error(errMsg(e));
    }
  };
  return (
    <>
      <PageHeader title="Audit logs" subtitle="Append-only trail of security-sensitive and operational events.">
        <button className="btn ghost" onClick={exportCsv} data-testid="export-audit-button"><Download size={15} /> Export CSV</button>
      </PageHeader>
      <div className="note-box small" style={{ marginBottom: 14 }}><Lock size={12} /> Read-only. MySQL triggers reject any UPDATE or DELETE on audit_logs, and the API exposes no write endpoints.</div>
      <div className="toolbar">
        <Select value={list.filters.action} onChange={(v) => list.update("action", v)} placeholder="All actions" options={actions} testid="audit-action-filter" />
        <Select value={list.filters.entity_type} onChange={(v) => list.update("entity_type", v)} placeholder="All entities" options={["user", "device", "telemetry", "alert", "incident", "prediction", "engineer_action", "site", "report", "audit_logs"]} testid="audit-entity-filter" />
        <Field label="From"><input className="input" type="datetime-local" value={list.filters.date_from} onChange={(e) => list.update("date_from", e.target.value)} data-testid="audit-from-filter" /></Field>
        <Field label="To"><input className="input" type="datetime-local" value={list.filters.date_to} onChange={(e) => list.update("date_to", e.target.value)} data-testid="audit-to-filter" /></Field>
      </div>
      <ErrorBox error={list.error} />
      <DataTable rowKey="audit_id" rows={list.items} loading={list.loading} testid="audit-table" columns={[
        { key: "audit_id", label: "#", num: true },
        { key: "created_at", label: "Time", render: (a) => fmtDate(a.created_at) },
        { key: "user_email", label: "User", render: (a) => a.user_email || "system / anonymous" },
        { key: "action", label: "Action", render: (a) => <strong>{a.action.replace(/_/g, " ")}</strong> },
        { key: "entity", label: "Entity", render: (a) => <span className="mono small">{a.entity_type}{a.entity_id ? ` #${a.entity_id}` : ""}</span> },
        { key: "details", label: "Details", hideSm: true, render: (a) => <span className="mono small" style={{ wordBreak: "break-all" }}>{a.details}</span> },
        { key: "ip_address", label: "IP", hideSm: true, num: true },
      ]} />
      <Pager {...list} testid="audit-pager" />
    </>
  );
}
