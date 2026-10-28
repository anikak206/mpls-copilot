# Relational Schema (generated from ORM metadata)

Notation: **PK** underlined-equivalent in bold, *FK* in italics with reference.

- **ROLES**(**role_id**, name, description)
- **SITES**(**site_id**, name, region, address)
- **USERS**(**user_id**, *role_id* → roles.role_id, email, full_name, password_hash, is_active, created_at, last_login_at)
- **AUDIT_LOGS**(**audit_id**, *user_id* → users.user_id, action, entity_type, entity_id, details, ip_address, created_at)
- **DEVICES**(**device_id**, hostname, mgmt_ip, device_type, vendor, model, *site_id* → sites.site_id, *assigned_engineer_id* → users.user_id, status, created_at, updated_at)
- **REVOKED_TOKENS**(**jti**, *user_id* → users.user_id, expires_at, revoked_at)
- **INCIDENTS**(**incident_id**, *device_id* → devices.device_id, title, description, severity, status, *opened_by* → users.user_id, *assigned_to* → users.user_id, opened_at, closed_at)
- **TELEMETRY**(**telemetry_id**, *device_id* → devices.device_id, recorded_at, cpu_util, mem_util, latency_ms, jitter_ms, packet_loss_pct, throughput_mbps, crc_errors, lsp_flaps, bgp_flaps, source, *recorded_by* → users.user_id)
- **PREDICTIONS**(**prediction_id**, *telemetry_id* → telemetry.telemetry_id, model_version, mode, label, anomaly_score, risk_score, risk_level, explanation, *requested_by* → users.user_id, created_at)
- **ALERTS**(**alert_id**, *device_id* → devices.device_id, *telemetry_id* → telemetry.telemetry_id, *prediction_id* → predictions.prediction_id, *incident_id* → incidents.incident_id, severity, source, message, status, *acknowledged_by* → users.user_id, created_at, resolved_at)
- **RECOMMENDATIONS**(**recommendation_id**, *prediction_id* → predictions.prediction_id, action_code, title, rationale, priority, created_at)
- **ENGINEER_ACTIONS**(**action_id**, *device_id* → devices.device_id, *recommendation_id* → recommendations.recommendation_id, *incident_id* → incidents.incident_id, *engineer_id* → users.user_id, action_type, description, performed_at)
- **OUTCOMES**(**outcome_id**, *action_id* → engineer_actions.action_id, result, notes, *recorded_by* → users.user_id, recorded_at)
