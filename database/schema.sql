-- ============================================================
-- Air-Gapped Predictive Copilot for Secure MPLS Operations
-- Phase 2: Database & Data Layer — MySQL Schema
-- ============================================================
-- Notes:
--  * InnoDB used throughout for FK support and transactions.
--  * utf8mb4 for full Unicode support.
--  * JSON columns used where flexible structured data is expected
--    (contributing factors, audit details) — MySQL 5.7.8+/8.0 required.
--  * Timestamps default to CURRENT_TIMESTAMP; adjust for your DB server's
--    timezone configuration.
-- ============================================================

CREATE DATABASE IF NOT EXISTS mpls_copilot
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mpls_copilot;

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------
-- 1. Roles
-- ------------------------------------------------------------
CREATE TABLE roles (
  role_id       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  role_name     VARCHAR(50)  NOT NULL UNIQUE,   -- 'admin', 'network_engineer', 'viewer'
  description   VARCHAR(255),
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 2. Users
-- ------------------------------------------------------------
CREATE TABLE users (
  user_id        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username       VARCHAR(64)  NOT NULL UNIQUE,
  password_hash  VARCHAR(255) NOT NULL,          -- bcrypt/argon2 hash, never plaintext
  full_name      VARCHAR(120) NOT NULL,
  email          VARCHAR(120),
  role_id        INT UNSIGNED NOT NULL,
  is_active      TINYINT(1)   NOT NULL DEFAULT 1,
  created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at  TIMESTAMP    NULL,
  CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(role_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX idx_users_role ON users(role_id);

-- ------------------------------------------------------------
-- 3. Devices
-- ------------------------------------------------------------
CREATE TABLE devices (
  device_id      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  hostname       VARCHAR(120) NOT NULL UNIQUE,
  vendor         VARCHAR(60)  NOT NULL,          -- 'Cisco', 'Juniper', ...
  model          VARCHAR(80),
  mgmt_ip        VARCHAR(45)  NOT NULL,          -- supports IPv4/IPv6
  device_role    VARCHAR(40),                    -- 'PE', 'P', 'CE', 'switch'
  site           VARCHAR(120),
  is_active      TINYINT(1)   NOT NULL DEFAULT 1,
  created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE INDEX idx_devices_vendor ON devices(vendor);
CREATE INDEX idx_devices_active ON devices(is_active);

-- ------------------------------------------------------------
-- 4. Telemetry (high-volume time-series metrics)
-- ------------------------------------------------------------
CREATE TABLE telemetry (
  telemetry_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  device_id      INT UNSIGNED NOT NULL,
  metric_type    VARCHAR(40)  NOT NULL,          -- 'cpu', 'memory', 'latency', 'packet_loss', ...
  metric_value   DECIMAL(12,4) NOT NULL,
  unit           VARCHAR(20),                    -- '%', 'ms', 'Mbps', ...
  collected_at   TIMESTAMP    NOT NULL,
  CONSTRAINT fk_telemetry_device FOREIGN KEY (device_id) REFERENCES devices(device_id)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_telemetry_device_time ON telemetry(device_id, collected_at);
CREATE INDEX idx_telemetry_metric_type ON telemetry(metric_type);

-- ------------------------------------------------------------
-- 5. Alerts
-- ------------------------------------------------------------
CREATE TABLE alerts (
  alert_id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  device_id      INT UNSIGNED NOT NULL,
  alert_type     VARCHAR(60)  NOT NULL,          -- 'link_down', 'high_cpu', 'anomaly', ...
  severity       ENUM('info','warning','critical') NOT NULL DEFAULT 'warning',
  message        VARCHAR(500) NOT NULL,
  status         ENUM('open','acknowledged','closed') NOT NULL DEFAULT 'open',
  triggered_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at    TIMESTAMP    NULL,
  CONSTRAINT fk_alerts_device FOREIGN KEY (device_id) REFERENCES devices(device_id)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_alerts_device_status ON alerts(device_id, status);
CREATE INDEX idx_alerts_severity ON alerts(severity);

-- ------------------------------------------------------------
-- 6. Incidents
-- ------------------------------------------------------------
CREATE TABLE incidents (
  incident_id    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  device_id      INT UNSIGNED NOT NULL,
  alert_id       BIGINT UNSIGNED NULL,
  title          VARCHAR(200) NOT NULL,
  description    TEXT,
  status         ENUM('open','in_progress','resolved','closed') NOT NULL DEFAULT 'open',
  opened_by      INT UNSIGNED NULL,
  opened_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  closed_at      TIMESTAMP    NULL,
  CONSTRAINT fk_incidents_device FOREIGN KEY (device_id) REFERENCES devices(device_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_incidents_alert FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_incidents_opened_by FOREIGN KEY (opened_by) REFERENCES users(user_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX idx_incidents_device_status ON incidents(device_id, status);

-- ------------------------------------------------------------
-- 7. Predictions
-- ------------------------------------------------------------
CREATE TABLE predictions (
  prediction_id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  device_id           INT UNSIGNED NOT NULL,
  incident_id         INT UNSIGNED NULL,
  model_version       VARCHAR(40)  NOT NULL,
  risk_score          DECIMAL(5,4) NOT NULL,      -- 0.0000–1.0000
  risk_level          ENUM('low','medium','high','critical') NOT NULL,
  prediction_horizon  VARCHAR(40),                 -- e.g. 'next_24h'
  contributing_factors JSON,                       -- explainability payload (feature: weight)
  predicted_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_predictions_device FOREIGN KEY (device_id) REFERENCES devices(device_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_predictions_incident FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX idx_predictions_device_time ON predictions(device_id, predicted_at);
CREATE INDEX idx_predictions_risk_level ON predictions(risk_level);

-- ------------------------------------------------------------
-- 8. Recommendations
-- ------------------------------------------------------------
CREATE TABLE recommendations (
  recommendation_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  prediction_id       BIGINT UNSIGNED NOT NULL,
  recommendation_text VARCHAR(1000) NOT NULL,
  priority            ENUM('low','medium','high') NOT NULL DEFAULT 'medium',
  created_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_recommendations_prediction FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_recommendations_prediction ON recommendations(prediction_id);

-- ------------------------------------------------------------
-- 9. Engineer Actions
-- ------------------------------------------------------------
CREATE TABLE engineer_actions (
  action_id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  prediction_id      BIGINT UNSIGNED NOT NULL,
  recommendation_id  INT UNSIGNED NULL,
  user_id            INT UNSIGNED NOT NULL,
  action_taken        VARCHAR(500) NOT NULL,
  action_notes       TEXT,
  action_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_actions_prediction FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_actions_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_actions_user FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX idx_actions_prediction ON engineer_actions(prediction_id);
CREATE INDEX idx_actions_user ON engineer_actions(user_id);

-- ------------------------------------------------------------
-- 10. Outcomes (prediction vs. reality — feeds the feedback loop)
-- ------------------------------------------------------------
CREATE TABLE outcomes (
  outcome_id       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  prediction_id    BIGINT UNSIGNED NOT NULL,
  actual_result    ENUM('failure_occurred','no_failure','false_positive','unknown') NOT NULL,
  outcome_notes    TEXT,
  recorded_by      INT UNSIGNED NULL,
  recorded_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_outcomes_prediction FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_outcomes_user FOREIGN KEY (recorded_by) REFERENCES users(user_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE UNIQUE INDEX uq_outcomes_prediction ON outcomes(prediction_id); -- one outcome per prediction
CREATE INDEX idx_outcomes_result ON outcomes(actual_result);

-- ------------------------------------------------------------
-- 11. Audit Log (append-only; covers all sensitive actions)
-- ------------------------------------------------------------
CREATE TABLE audit_log (
  audit_id      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       INT UNSIGNED NULL,               -- NULL = system-generated event
  entity_type   VARCHAR(60)  NOT NULL,            -- 'prediction', 'user', 'device', 'alert', ...
  entity_id     BIGINT UNSIGNED NOT NULL,
  action        VARCHAR(60)  NOT NULL,            -- 'create', 'update', 'delete', 'login', 'view', ...
  details       JSON,                             -- before/after values, request metadata
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);

SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- Seed data: default roles
-- ------------------------------------------------------------
INSERT INTO roles (role_name, description) VALUES
  ('admin', 'System owner / configuration authority'),
  ('network_engineer', 'Day-to-day operator responding to alerts'),
  ('viewer', 'Read-only stakeholder');

-- Example admin user (replace password_hash with a real bcrypt/argon2 hash before use)
INSERT INTO users (username, password_hash, full_name, role_id)
VALUES ('admin', '$2b$12$REPLACE_WITH_REAL_HASH', 'System Administrator',
        (SELECT role_id FROM roles WHERE role_name = 'admin'));
