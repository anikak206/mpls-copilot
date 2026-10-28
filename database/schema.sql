-- Air-Gapped Predictive Copilot for Secure MPLS Operations
-- MySQL 8 / MariaDB 10.6+ schema (13 tables). Exported from the migrated database (Alembic 0001_baseline).
-- Load order: schema.sql -> views.sql -> procedures.sql -> triggers.sql -> seed.sql
SET FOREIGN_KEY_CHECKS = 0;
/*M!999999\- enable the sandbox mode */ 
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `alerts` (
  `alert_id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` int(11) NOT NULL,
  `telemetry_id` int(11) DEFAULT NULL,
  `prediction_id` int(11) DEFAULT NULL,
  `incident_id` int(11) DEFAULT NULL,
  `severity` varchar(8) NOT NULL,
  `source` varchar(7) NOT NULL,
  `message` varchar(255) NOT NULL,
  `status` varchar(12) NOT NULL DEFAULT 'open',
  `acknowledged_by` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `resolved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`alert_id`),
  KEY `telemetry_id` (`telemetry_id`),
  KEY `prediction_id` (`prediction_id`),
  KEY `acknowledged_by` (`acknowledged_by`),
  KEY `ix_alerts_created` (`created_at`),
  KEY `ix_alerts_incident_id` (`incident_id`),
  KEY `ix_alerts_device_status` (`device_id`,`status`),
  CONSTRAINT `alerts_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`) ON DELETE CASCADE,
  CONSTRAINT `alerts_ibfk_2` FOREIGN KEY (`telemetry_id`) REFERENCES `telemetry` (`telemetry_id`) ON DELETE SET NULL,
  CONSTRAINT `alerts_ibfk_3` FOREIGN KEY (`prediction_id`) REFERENCES `predictions` (`prediction_id`) ON DELETE SET NULL,
  CONSTRAINT `alerts_ibfk_4` FOREIGN KEY (`incident_id`) REFERENCES `incidents` (`incident_id`) ON DELETE SET NULL,
  CONSTRAINT `alerts_ibfk_5` FOREIGN KEY (`acknowledged_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `ck_alert_severity` CHECK (`severity` in ('info','warning','major','critical')),
  CONSTRAINT `ck_alert_source` CHECK (`source` in ('trigger','ml','manual')),
  CONSTRAINT `ck_alert_status` CHECK (`status` in ('open','acknowledged','resolved'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `audit_logs` (
  `audit_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `action` varchar(60) NOT NULL,
  `entity_type` varchar(40) NOT NULL,
  `entity_id` varchar(120) DEFAULT NULL,
  `details` text DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`audit_id`),
  KEY `ix_audit_entity` (`entity_type`,`entity_id`),
  KEY `ix_audit_action` (`action`),
  KEY `ix_audit_logs_user_id` (`user_id`),
  KEY `ix_audit_created` (`created_at`),
  CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `devices` (
  `device_id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(64) NOT NULL,
  `mgmt_ip` varchar(45) NOT NULL,
  `device_type` varchar(4) NOT NULL,
  `vendor` varchar(40) NOT NULL,
  `model` varchar(60) NOT NULL,
  `site_id` int(11) NOT NULL,
  `assigned_engineer_id` int(11) DEFAULT NULL,
  `status` varchar(12) NOT NULL DEFAULT 'up',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`device_id`),
  UNIQUE KEY `hostname` (`hostname`),
  UNIQUE KEY `mgmt_ip` (`mgmt_ip`),
  KEY `ix_devices_assigned_engineer_id` (`assigned_engineer_id`),
  KEY `ix_devices_site_id` (`site_id`),
  KEY `ix_devices_status` (`status`),
  CONSTRAINT `devices_ibfk_1` FOREIGN KEY (`site_id`) REFERENCES `sites` (`site_id`),
  CONSTRAINT `devices_ibfk_2` FOREIGN KEY (`assigned_engineer_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `ck_devices_type` CHECK (`device_type` in ('PE','P','CE','RR')),
  CONSTRAINT `ck_devices_status` CHECK (`status` in ('up','degraded','down','maintenance'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `engineer_actions` (
  `action_id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` int(11) NOT NULL,
  `recommendation_id` int(11) DEFAULT NULL,
  `incident_id` int(11) DEFAULT NULL,
  `engineer_id` int(11) NOT NULL,
  `action_type` varchar(20) NOT NULL,
  `description` text NOT NULL,
  `performed_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`action_id`),
  KEY `engineer_id` (`engineer_id`),
  KEY `ix_engineer_actions_device_id` (`device_id`),
  KEY `ix_engineer_actions_recommendation_id` (`recommendation_id`),
  KEY `ix_engineer_actions_incident_id` (`incident_id`),
  CONSTRAINT `engineer_actions_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`) ON DELETE CASCADE,
  CONSTRAINT `engineer_actions_ibfk_2` FOREIGN KEY (`recommendation_id`) REFERENCES `recommendations` (`recommendation_id`) ON DELETE SET NULL,
  CONSTRAINT `engineer_actions_ibfk_3` FOREIGN KEY (`incident_id`) REFERENCES `incidents` (`incident_id`) ON DELETE SET NULL,
  CONSTRAINT `engineer_actions_ibfk_4` FOREIGN KEY (`engineer_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `ck_action_type` CHECK (`action_type` in ('config_change','interface_reset','traffic_reroute','hardware_check','escalation','monitoring','other'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `incidents` (
  `incident_id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` int(11) NOT NULL,
  `title` varchar(160) NOT NULL,
  `description` text NOT NULL,
  `severity` varchar(8) NOT NULL,
  `status` varchar(13) NOT NULL DEFAULT 'open',
  `opened_by` int(11) DEFAULT NULL,
  `assigned_to` int(11) DEFAULT NULL,
  `opened_at` datetime NOT NULL DEFAULT current_timestamp(),
  `closed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`incident_id`),
  KEY `opened_by` (`opened_by`),
  KEY `assigned_to` (`assigned_to`),
  KEY `ix_incidents_device_id` (`device_id`),
  KEY `ix_incidents_status` (`status`),
  CONSTRAINT `incidents_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`) ON DELETE CASCADE,
  CONSTRAINT `incidents_ibfk_2` FOREIGN KEY (`opened_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `incidents_ibfk_3` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `ck_inc_severity` CHECK (`severity` in ('info','warning','major','critical')),
  CONSTRAINT `ck_inc_status` CHECK (`status` in ('open','investigating','mitigated','closed'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `outcomes` (
  `outcome_id` int(11) NOT NULL AUTO_INCREMENT,
  `action_id` int(11) NOT NULL,
  `result` varchar(10) NOT NULL,
  `notes` text NOT NULL,
  `recorded_by` int(11) DEFAULT NULL,
  `recorded_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`outcome_id`),
  UNIQUE KEY `action_id` (`action_id`),
  KEY `recorded_by` (`recorded_by`),
  CONSTRAINT `outcomes_ibfk_1` FOREIGN KEY (`action_id`) REFERENCES `engineer_actions` (`action_id`) ON DELETE CASCADE,
  CONSTRAINT `outcomes_ibfk_2` FOREIGN KEY (`recorded_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `ck_outcome_result` CHECK (`result` in ('resolved','improved','no_change','worsened'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `predictions` (
  `prediction_id` int(11) NOT NULL AUTO_INCREMENT,
  `telemetry_id` int(11) NOT NULL,
  `model_version` varchar(40) NOT NULL,
  `mode` varchar(5) NOT NULL,
  `label` varchar(10) NOT NULL,
  `anomaly_score` float NOT NULL,
  `risk_score` float NOT NULL,
  `risk_level` varchar(8) NOT NULL,
  `explanation` text NOT NULL,
  `requested_by` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`prediction_id`),
  KEY `requested_by` (`requested_by`),
  KEY `ix_predictions_created` (`created_at`),
  KEY `ix_predictions_telemetry` (`telemetry_id`),
  KEY `ix_predictions_level` (`risk_level`),
  CONSTRAINT `predictions_ibfk_1` FOREIGN KEY (`telemetry_id`) REFERENCES `telemetry` (`telemetry_id`) ON DELETE CASCADE,
  CONSTRAINT `predictions_ibfk_2` FOREIGN KEY (`requested_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `ck_pred_mode` CHECK (`mode` in ('model','demo')),
  CONSTRAINT `ck_pred_label` CHECK (`label` in ('normal','anomalous','uncertain')),
  CONSTRAINT `ck_pred_risk` CHECK (`risk_score` between 0 and 100),
  CONSTRAINT `ck_pred_level` CHECK (`risk_level` in ('low','medium','high','critical'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `recommendations` (
  `recommendation_id` int(11) NOT NULL AUTO_INCREMENT,
  `prediction_id` int(11) NOT NULL,
  `action_code` varchar(40) NOT NULL,
  `title` varchar(160) NOT NULL,
  `rationale` text NOT NULL,
  `priority` varchar(8) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`recommendation_id`),
  UNIQUE KEY `prediction_id` (`prediction_id`),
  CONSTRAINT `recommendations_ibfk_1` FOREIGN KEY (`prediction_id`) REFERENCES `predictions` (`prediction_id`) ON DELETE CASCADE,
  CONSTRAINT `ck_rec_priority` CHECK (`priority` in ('low','medium','high','urgent'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `revoked_tokens` (
  `jti` varchar(36) NOT NULL,
  `user_id` int(11) NOT NULL,
  `expires_at` datetime NOT NULL,
  `revoked_at` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`jti`),
  KEY `ix_revoked_tokens_user_id` (`user_id`),
  CONSTRAINT `revoked_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `roles` (
  `role_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) NOT NULL,
  `description` varchar(255) NOT NULL,
  PRIMARY KEY (`role_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `sites` (
  `site_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  `region` varchar(80) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`site_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `telemetry` (
  `telemetry_id` int(11) NOT NULL AUTO_INCREMENT,
  `device_id` int(11) NOT NULL,
  `recorded_at` datetime NOT NULL DEFAULT current_timestamp(),
  `cpu_util` float NOT NULL,
  `mem_util` float NOT NULL,
  `latency_ms` float NOT NULL,
  `jitter_ms` float NOT NULL,
  `packet_loss_pct` float NOT NULL,
  `throughput_mbps` float NOT NULL,
  `crc_errors` int(11) NOT NULL DEFAULT 0,
  `lsp_flaps` int(11) NOT NULL DEFAULT 0,
  `bgp_flaps` int(11) NOT NULL DEFAULT 0,
  `source` varchar(10) NOT NULL DEFAULT 'collector',
  `recorded_by` int(11) DEFAULT NULL,
  PRIMARY KEY (`telemetry_id`),
  KEY `recorded_by` (`recorded_by`),
  KEY `ix_telemetry_time` (`recorded_at`),
  KEY `ix_telemetry_device_time` (`device_id`,`recorded_at`),
  CONSTRAINT `telemetry_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`) ON DELETE CASCADE,
  CONSTRAINT `telemetry_ibfk_2` FOREIGN KEY (`recorded_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `ck_tel_cpu` CHECK (`cpu_util` between 0 and 100),
  CONSTRAINT `ck_tel_mem` CHECK (`mem_util` between 0 and 100),
  CONSTRAINT `ck_tel_latency` CHECK (`latency_ms` >= 0 and `latency_ms` <= 10000),
  CONSTRAINT `ck_tel_jitter` CHECK (`jitter_ms` >= 0 and `jitter_ms` <= 5000),
  CONSTRAINT `ck_tel_loss` CHECK (`packet_loss_pct` between 0 and 100),
  CONSTRAINT `ck_tel_throughput` CHECK (`throughput_mbps` >= 0),
  CONSTRAINT `ck_tel_counters` CHECK (`crc_errors` >= 0 and `lsp_flaps` >= 0 and `bgp_flaps` >= 0),
  CONSTRAINT `ck_tel_source` CHECK (`source` in ('manual','collector','seed'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE IF NOT EXISTS `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `role_id` int(11) NOT NULL,
  `email` varchar(120) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `last_login_at` datetime DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `ix_users_role_id` (`role_id`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`role_id`),
  CONSTRAINT `ck_users_email_format` CHECK (`email` like '%_@_%')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
SET FOREIGN_KEY_CHECKS = 1;
