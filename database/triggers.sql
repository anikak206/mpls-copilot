-- Triggers. Run with: mysql -u <user> -p <db> < database/triggers.sql

DROP TRIGGER IF EXISTS trg_telemetry_threshold_alert;
DROP TRIGGER IF EXISTS trg_incident_before_update;
DROP TRIGGER IF EXISTS trg_incident_status_audit;
DROP TRIGGER IF EXISTS trg_audit_logs_no_update;
DROP TRIGGER IF EXISTS trg_audit_logs_no_delete;

DELIMITER $$

-- 1. Derived record: a telemetry sample breaching hard thresholds raises an alert automatically.
CREATE TRIGGER trg_telemetry_threshold_alert
AFTER INSERT ON telemetry
FOR EACH ROW
BEGIN
    IF NEW.packet_loss_pct >= 5 OR NEW.cpu_util >= 95 OR NEW.lsp_flaps >= 5 THEN
        INSERT INTO alerts (device_id, telemetry_id, severity, source, message)
        VALUES (NEW.device_id, NEW.telemetry_id, 'critical', 'trigger',
                CONCAT('Critical threshold breach: loss=', ROUND(NEW.packet_loss_pct, 2), '%, cpu=',
                       ROUND(NEW.cpu_util, 1), '%, lsp_flaps=', NEW.lsp_flaps));
    ELSEIF NEW.packet_loss_pct >= 2 OR NEW.cpu_util >= 85 OR NEW.latency_ms >= 150 THEN
        INSERT INTO alerts (device_id, telemetry_id, severity, source, message)
        VALUES (NEW.device_id, NEW.telemetry_id, 'major', 'trigger',
                CONCAT('Threshold breach: loss=', ROUND(NEW.packet_loss_pct, 2), '%, cpu=',
                       ROUND(NEW.cpu_util, 1), '%, latency=', ROUND(NEW.latency_ms, 1), 'ms'));
    END IF;
END$$

-- 2. Maintain closed_at automatically when an incident is closed / reopened.
CREATE TRIGGER trg_incident_before_update
BEFORE UPDATE ON incidents
FOR EACH ROW
BEGIN
    IF NEW.status = 'closed' AND OLD.status <> 'closed' THEN
        SET NEW.closed_at = NOW();
    ELSEIF NEW.status <> 'closed' THEN
        SET NEW.closed_at = NULL;
    END IF;
END$$

-- 3. Audit event for incident status changes. The application does NOT log status changes
--    itself, so there is exactly one audit row per change. Actor comes from @app_user_id.
CREATE TRIGGER trg_incident_status_audit
AFTER UPDATE ON incidents
FOR EACH ROW
BEGIN
    IF NOT (OLD.status <=> NEW.status) THEN
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
        VALUES (@app_user_id, 'incident_status_changed', 'incident', NEW.incident_id,
                CONCAT(OLD.status, ' -> ', NEW.status));
    END IF;
END$$

-- 4/5. Audit trail is append-only.
CREATE TRIGGER trg_audit_logs_no_update
BEFORE UPDATE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'audit_logs is append-only';
END$$

CREATE TRIGGER trg_audit_logs_no_delete
BEFORE DELETE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'audit_logs is append-only';
END$$

DELIMITER ;

-- Test:
-- INSERT INTO telemetry (device_id, cpu_util, mem_util, latency_ms, jitter_ms, packet_loss_pct, throughput_mbps, source)
--   VALUES (1, 97, 60, 20, 2, 0.1, 1000, 'manual');
-- SELECT * FROM alerts ORDER BY alert_id DESC LIMIT 1;           -- new critical alert
-- SET @app_user_id = 1; UPDATE incidents SET status='closed' WHERE incident_id = 1;
-- SELECT * FROM audit_logs WHERE action='incident_status_changed' ORDER BY audit_id DESC LIMIT 1;
-- DELETE FROM audit_logs WHERE audit_id = 1;                      -- fails: append-only
