# Data Dictionary (generated from ORM metadata)

## roles

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| role_id | INTEGER | NO | PK |  |  |
| name | VARCHAR(40) | NO | UQ |  |  |
| description | VARCHAR(255) | NO |  |  |  |

## sites

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| site_id | INTEGER | NO | PK |  |  |
| name | VARCHAR(80) | NO | UQ |  |  |
| region | VARCHAR(80) | NO |  |  |  |
| address | VARCHAR(255) | YES |  |  |  |

## users

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| user_id | INTEGER | NO | PK |  |  |
| role_id | INTEGER | NO | FK |  | roles.role_id ON DELETE RESTRICT |
| email | VARCHAR(120) | NO | UQ |  |  |
| full_name | VARCHAR(100) | NO |  |  |  |
| password_hash | VARCHAR(255) | NO |  |  |  |
| is_active | BOOL | NO |  | 1 |  |
| created_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |
| last_login_at | DATETIME | YES |  |  |  |

CHECK constraints: `email LIKE '%_@_%'`

Indexes: `ix_users_role_id` (role_id)

## audit_logs

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| audit_id | INTEGER | NO | PK |  |  |
| user_id | INTEGER | YES | FK |  | users.user_id ON DELETE SET NULL |
| action | VARCHAR(60) | NO |  |  |  |
| entity_type | VARCHAR(40) | NO |  |  |  |
| entity_id | VARCHAR(120) | YES |  |  |  |
| details | TEXT | YES |  |  |  |
| ip_address | VARCHAR(45) | YES |  |  |  |
| created_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |

Indexes: `ix_audit_logs_user_id` (user_id), `ix_audit_entity` (entity_type, entity_id), `ix_audit_action` (action), `ix_audit_created` (created_at)

## devices

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| device_id | INTEGER | NO | PK |  |  |
| hostname | VARCHAR(64) | NO | UQ |  |  |
| mgmt_ip | VARCHAR(45) | NO | UQ |  |  |
| device_type | VARCHAR(4) | NO |  |  |  |
| vendor | VARCHAR(40) | NO |  |  |  |
| model | VARCHAR(60) | NO |  |  |  |
| site_id | INTEGER | NO | FK |  | sites.site_id ON DELETE RESTRICT |
| assigned_engineer_id | INTEGER | YES | FK |  | users.user_id ON DELETE SET NULL |
| status | VARCHAR(12) | NO |  | up |  |
| created_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |

CHECK constraints: `device_type IN ('PE','P','CE','RR')`; `status IN ('up','degraded','down','maintenance')`

Indexes: `ix_devices_assigned_engineer_id` (assigned_engineer_id), `ix_devices_site_id` (site_id), `ix_devices_status` (status)

## revoked_tokens

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| jti | VARCHAR(36) | NO | PK |  |  |
| user_id | INTEGER | NO | FK |  | users.user_id ON DELETE CASCADE |
| expires_at | DATETIME | NO |  |  |  |
| revoked_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |

Indexes: `ix_revoked_tokens_user_id` (user_id)

## incidents

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| incident_id | INTEGER | NO | PK |  |  |
| device_id | INTEGER | NO | FK |  | devices.device_id ON DELETE CASCADE |
| title | VARCHAR(160) | NO |  |  |  |
| description | TEXT | NO |  |  |  |
| severity | VARCHAR(8) | NO |  |  |  |
| status | VARCHAR(13) | NO |  | open |  |
| opened_by | INTEGER | YES | FK |  | users.user_id ON DELETE SET NULL |
| assigned_to | INTEGER | YES | FK |  | users.user_id ON DELETE SET NULL |
| opened_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |
| closed_at | DATETIME | YES |  |  |  |

CHECK constraints: `severity IN ('info','warning','major','critical')`; `status IN ('open','investigating','mitigated','closed')`

Indexes: `ix_incidents_status` (status), `ix_incidents_device_id` (device_id)

## telemetry

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| telemetry_id | INTEGER | NO | PK |  |  |
| device_id | INTEGER | NO | FK |  | devices.device_id ON DELETE CASCADE |
| recorded_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |
| cpu_util | FLOAT | NO |  |  |  |
| mem_util | FLOAT | NO |  |  |  |
| latency_ms | FLOAT | NO |  |  |  |
| jitter_ms | FLOAT | NO |  |  |  |
| packet_loss_pct | FLOAT | NO |  |  |  |
| throughput_mbps | FLOAT | NO |  |  |  |
| crc_errors | INTEGER | NO |  | 0 |  |
| lsp_flaps | INTEGER | NO |  | 0 |  |
| bgp_flaps | INTEGER | NO |  | 0 |  |
| source | VARCHAR(10) | NO |  | collector |  |
| recorded_by | INTEGER | YES | FK |  | users.user_id ON DELETE SET NULL |

CHECK constraints: `mem_util BETWEEN 0 AND 100`; `latency_ms >= 0 AND latency_ms <= 10000`; `packet_loss_pct BETWEEN 0 AND 100`; `throughput_mbps >= 0`; `crc_errors >= 0 AND lsp_flaps >= 0 AND bgp_flaps >= 0`; `source IN ('manual','collector','seed')`; `cpu_util BETWEEN 0 AND 100`; `jitter_ms >= 0 AND jitter_ms <= 5000`

Indexes: `ix_telemetry_device_time` (device_id, recorded_at), `ix_telemetry_time` (recorded_at)

## predictions

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| prediction_id | INTEGER | NO | PK |  |  |
| telemetry_id | INTEGER | NO | FK |  | telemetry.telemetry_id ON DELETE CASCADE |
| model_version | VARCHAR(40) | NO |  |  |  |
| mode | VARCHAR(5) | NO |  |  |  |
| label | VARCHAR(10) | NO |  |  |  |
| anomaly_score | FLOAT | NO |  |  |  |
| risk_score | FLOAT | NO |  |  |  |
| risk_level | VARCHAR(8) | NO |  |  |  |
| explanation | TEXT | NO |  |  |  |
| requested_by | INTEGER | YES | FK |  | users.user_id ON DELETE SET NULL |
| created_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |

CHECK constraints: `label IN ('normal','anomalous','uncertain')`; `risk_score BETWEEN 0 AND 100`; `risk_level IN ('low','medium','high','critical')`; `mode IN ('model','demo')`

Indexes: `ix_predictions_created` (created_at), `ix_predictions_telemetry` (telemetry_id), `ix_predictions_level` (risk_level)

## alerts

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| alert_id | INTEGER | NO | PK |  |  |
| device_id | INTEGER | NO | FK |  | devices.device_id ON DELETE CASCADE |
| telemetry_id | INTEGER | YES | FK |  | telemetry.telemetry_id ON DELETE SET NULL |
| prediction_id | INTEGER | YES | FK |  | predictions.prediction_id ON DELETE SET NULL |
| incident_id | INTEGER | YES | FK |  | incidents.incident_id ON DELETE SET NULL |
| severity | VARCHAR(8) | NO |  |  |  |
| source | VARCHAR(7) | NO |  |  |  |
| message | VARCHAR(255) | NO |  |  |  |
| status | VARCHAR(12) | NO |  | open |  |
| acknowledged_by | INTEGER | YES | FK |  | users.user_id ON DELETE SET NULL |
| created_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |
| resolved_at | DATETIME | YES |  |  |  |

CHECK constraints: `source IN ('trigger','ml','manual')`; `status IN ('open','acknowledged','resolved')`; `severity IN ('info','warning','major','critical')`

Indexes: `ix_alerts_created` (created_at), `ix_alerts_incident_id` (incident_id), `ix_alerts_device_status` (device_id, status)

## recommendations

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| recommendation_id | INTEGER | NO | PK |  |  |
| prediction_id | INTEGER | NO | FK |  | predictions.prediction_id ON DELETE CASCADE |
| action_code | VARCHAR(40) | NO |  |  |  |
| title | VARCHAR(160) | NO |  |  |  |
| rationale | TEXT | NO |  |  |  |
| priority | VARCHAR(8) | NO |  |  |  |
| created_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |

CHECK constraints: `priority IN ('low','medium','high','urgent')`

## engineer_actions

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| action_id | INTEGER | NO | PK |  |  |
| device_id | INTEGER | NO | FK |  | devices.device_id ON DELETE CASCADE |
| recommendation_id | INTEGER | YES | FK |  | recommendations.recommendation_id ON DELETE SET NULL |
| incident_id | INTEGER | YES | FK |  | incidents.incident_id ON DELETE SET NULL |
| engineer_id | INTEGER | NO | FK |  | users.user_id ON DELETE RESTRICT |
| action_type | VARCHAR(20) | NO |  |  |  |
| description | TEXT | NO |  |  |  |
| performed_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |

CHECK constraints: `action_type IN ('config_change','interface_reset','traffic_reroute','hardware_check','escalation','monitoring','other')`

Indexes: `ix_engineer_actions_device_id` (device_id), `ix_engineer_actions_recommendation_id` (recommendation_id), `ix_engineer_actions_incident_id` (incident_id)

## outcomes

| Column | Type | Null | Key | Default | References |
|---|---|---|---|---|---|
| outcome_id | INTEGER | NO | PK |  |  |
| action_id | INTEGER | NO | FK |  | engineer_actions.action_id ON DELETE CASCADE |
| result | VARCHAR(10) | NO |  |  |  |
| notes | TEXT | NO |  |  |  |
| recorded_by | INTEGER | YES | FK |  | users.user_id ON DELETE SET NULL |
| recorded_at | DATETIME | NO |  | CURRENT_TIMESTAMP |  |

CHECK constraints: `result IN ('resolved','improved','no_change','worsened')`
