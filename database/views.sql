-- Reporting views (MySQL 8 / MariaDB 10.6+)

-- v_device_health: one row per device with site, engineer, 24h telemetry averages,
-- open alert count and most recent ML risk assessment.
CREATE OR REPLACE VIEW v_device_health AS
SELECT d.device_id,
       d.hostname,
       d.mgmt_ip,
       d.device_type,
       d.status,
       s.name AS site_name,
       s.region,
       u.full_name AS assigned_engineer,
       (SELECT COUNT(*) FROM alerts a
         WHERE a.device_id = d.device_id AND a.status <> 'resolved') AS open_alerts,
       (SELECT ROUND(AVG(t.cpu_util), 2) FROM telemetry t
         WHERE t.device_id = d.device_id AND t.recorded_at >= NOW() - INTERVAL 1 DAY) AS avg_cpu_24h,
       (SELECT ROUND(AVG(t.latency_ms), 2) FROM telemetry t
         WHERE t.device_id = d.device_id AND t.recorded_at >= NOW() - INTERVAL 1 DAY) AS avg_latency_24h,
       (SELECT ROUND(AVG(t.packet_loss_pct), 3) FROM telemetry t
         WHERE t.device_id = d.device_id AND t.recorded_at >= NOW() - INTERVAL 1 DAY) AS avg_loss_24h,
       (SELECT p.risk_score FROM predictions p JOIN telemetry t2 ON t2.telemetry_id = p.telemetry_id
         WHERE t2.device_id = d.device_id ORDER BY p.created_at DESC, p.prediction_id DESC LIMIT 1) AS latest_risk_score,
       (SELECT p.risk_level FROM predictions p JOIN telemetry t2 ON t2.telemetry_id = p.telemetry_id
         WHERE t2.device_id = d.device_id ORDER BY p.created_at DESC, p.prediction_id DESC LIMIT 1) AS latest_risk_level
FROM devices d
JOIN sites s ON s.site_id = d.site_id
LEFT JOIN users u ON u.user_id = d.assigned_engineer_id;

-- v_prediction_report: prediction joined with its telemetry sample, device, site,
-- recommendation and the requesting user.
CREATE OR REPLACE VIEW v_prediction_report AS
SELECT p.prediction_id,
       p.created_at,
       p.label,
       p.risk_score,
       p.risk_level,
       p.mode,
       p.model_version,
       t.telemetry_id,
       t.recorded_at,
       d.device_id,
       d.hostname,
       s.name AS site_name,
       r.recommendation_id,
       r.title AS recommendation,
       r.priority,
       u.full_name AS requested_by
FROM predictions p
JOIN telemetry t ON t.telemetry_id = p.telemetry_id
JOIN devices d ON d.device_id = t.device_id
JOIN sites s ON s.site_id = d.site_id
LEFT JOIN recommendations r ON r.prediction_id = p.prediction_id
LEFT JOIN users u ON u.user_id = p.requested_by;

-- Demonstration queries:
-- SELECT * FROM v_device_health ORDER BY latest_risk_score DESC;
-- SELECT risk_level, COUNT(*) FROM v_prediction_report GROUP BY risk_level;
