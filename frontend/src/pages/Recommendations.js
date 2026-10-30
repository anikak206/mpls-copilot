import { useState } from "react";
import { Wrench } from "lucide-react";
import { ROLES, useAuth } from "../context/AuthContext";
import { fmtDate } from "../lib/api";
import { useList } from "../lib/hooks";
import { DataTable, ErrorBox, Modal, PageHeader, Pager, Pill, Select } from "../components/kit";
import { ActionForm } from "./Actions";

export default function Recommendations() {
  const { hasRole } = useAuth();
  const canAct = hasRole(ROLES.ADMIN, ROLES.ENGINEER);
  const list = useList("/recommendations", { priority: "" }, 12);
  const [acting, setActing] = useState(null);
  return (
    <>
      <PageHeader title="Recommendations" subtitle="Advisory next steps derived from each prediction's dominant signal. Always validate before acting." />
      <div className="toolbar">
        <Select value={list.filters.priority} onChange={(v) => list.update("priority", v)} placeholder="All priorities" options={["low", "medium", "high", "urgent"]} testid="recommendation-priority-filter" />
      </div>
      <ErrorBox error={list.error} />
      <DataTable rowKey="recommendation_id" rows={list.items} loading={list.loading} testid="recommendations-table" columns={[
        { key: "recommendation_id", label: "#", num: true },
        { key: "hostname", label: "Device", render: (r) => <strong>{r.hostname}</strong> },
        { key: "title", label: "Recommendation", render: (r) => <div><strong>{r.title}</strong><div className="small muted" style={{ maxWidth: 560 }}>{r.rationale}</div></div> },
        { key: "priority", label: "Priority", render: (r) => <Pill value={r.priority} /> },
        { key: "pred", label: "Prediction", render: (r) => <span><Pill value={r.label} /> <span className="mono small">#{r.prediction_id} · {r.risk_score}</span></span> },
        { key: "created_at", label: "Created", hideSm: true, render: (r) => fmtDate(r.created_at) },
        { key: "ops", label: "", render: (r) => canAct && <button className="btn sm" onClick={() => setActing(r)} data-testid={`act-on-recommendation-${r.recommendation_id}`}><Wrench size={13} /> Record action</button> },
      ]} />
      <Pager {...list} testid="recommendations-pager" />
      <Modal open={!!acting} title="Record engineer action" onClose={() => setActing(null)} testid="recommendation-action-modal">
        {acting && <ActionForm preset={{ device_id: acting.device_id, recommendation_id: acting.recommendation_id }} onClose={() => setActing(null)} onSaved={() => setActing(null)} />}
      </Modal>
    </>
  );
}
