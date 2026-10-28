-- Stored procedures. Run with: mysql -u <user> -p <db> < database/procedures.sql

DROP PROCEDURE IF EXISTS sp_open_incident_from_alert;
DROP PROCEDURE IF EXISTS sp_device_risk_summary;

DELIMITER $$

-- Escalates an alert into an incident atomically: inserts the incident, links and
-- acknowledges the alert, and writes an audit record. Any failure rolls back all three.
CREATE PROCEDURE sp_open_incident_from_alert(IN p_alert_id INT, IN p_user_id INT, OUT p_incident_id INT)
BEGIN
    DECLARE v_device INT DEFAULT NULL;
    DECLARE v_severity VARCHAR(8);
    DECLARE v_message VARCHAR(255);
    DECLARE v_existing INT DEFAULT NULL;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
    SELECT device_id, severity, message, incident_id
      INTO v_device, v_severity, v_message, v_existing
      FROM alerts WHERE alert_id = p_alert_id FOR UPDATE;

    IF v_device IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Alert not found';
    END IF;
    IF v_existing IS NOT NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Alert is already linked to an incident';
    END IF;

    INSERT INTO incidents (device_id, title, description, severity, status, opened_by)
    VALUES (v_device, LEFT(CONCAT('Escalated alert #', p_alert_id, ': ', v_message), 160),
            CONCAT('Opened from alert #', p_alert_id, '. ', v_message), v_severity, 'open', p_user_id);
    SET p_incident_id = LAST_INSERT_ID();

    UPDATE alerts SET incident_id = p_incident_id, status = 'acknowledged', acknowledged_by = p_user_id
     WHERE alert_id = p_alert_id;

    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
    VALUES (p_user_id, 'incident_opened_from_alert', 'incident', p_incident_id, CONCAT('alert_id=', p_alert_id));
    COMMIT;
END$$

-- Per-device risk summary over the last p_days days (aggregate + join report).
CREATE PROCEDURE sp_device_risk_summary(IN p_days INT)
BEGIN
    IF p_days IS NULL OR p_days < 1 OR p_days > 365 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'p_days must be between 1 and 365';
    END IF;
    SELECT d.device_id,
           d.hostname,
           s.name AS site_name,
           COUNT(p.prediction_id) AS predictions,
           COALESCE(SUM(p.label = 'anomalous'), 0) AS anomalies,
           ROUND(AVG(p.risk_score), 2) AS avg_risk,
           ROUND(MAX(p.risk_score), 2) AS max_risk
      FROM devices d
      JOIN sites s ON s.site_id = d.site_id
      LEFT JOIN telemetry t ON t.device_id = d.device_id
      LEFT JOIN predictions p ON p.telemetry_id = t.telemetry_id
                             AND p.created_at >= NOW() - INTERVAL p_days DAY
     GROUP BY d.device_id, d.hostname, s.name
     ORDER BY avg_risk DESC, d.hostname;
END$$

DELIMITER ;

-- Test:
-- CALL sp_open_incident_from_alert(1, 1, @inc); SELECT @inc;
-- CALL sp_device_risk_summary(7);
