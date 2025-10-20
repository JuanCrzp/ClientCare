-- ClientCare Bot - Esquema MySQL 8.0 Enterprise
-- Características: multi-tenant, escalable, auditado, compatible con utf8mb4
-- Requisitos: MySQL 8.0+, sql_mode estricto, InnoDB, timezone UTC

-- Configuración recomendada a nivel de base de datos
-- ALTER DATABASE `clientcare` CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
-- SET @@GLOBAL.time_zone = '+00:00';

-- Utilidad: generador de UUID (si la app no lo provee)
-- CREATE FUNCTION uuid_v4() RETURNS CHAR(36) DETERMINISTIC RETURN UUID();

-- Limpieza opcional (ejecutar con cuidado en entornos de desarrollo)
-- SET FOREIGN_KEY_CHECKS = 0;
-- DROP TABLE IF EXISTS webhook_deliveries, webhooks, config_versions,
--   nlu_logs, nlu_synonyms, nlu_intents, faq_articles, faq_categories,
--   ticket_tags, tags, ticket_events, messages, conversations,
--   tickets, agents, end_users, channels, tenants;
-- SET FOREIGN_KEY_CHECKS = 1;

-- Enums (MySQL ENUM) para consistencia
-- Nota: considera tablas de catálogo si prefieres mayor flexibilidad

-- Tenants/organizaciones
CREATE TABLE IF NOT EXISTS tenants (
	id CHAR(36) NOT NULL,
	name VARCHAR(128) NOT NULL,
	slug VARCHAR(64) NOT NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY uq_tenants_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Canales por tenant
CREATE TABLE IF NOT EXISTS channels (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	type ENUM('telegram','whatsapp','webchat') NOT NULL,
	external_id VARCHAR(128) NULL,
	display_name VARCHAR(128) NULL,
	is_active TINYINT(1) NOT NULL DEFAULT 1,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY idx_channels_tenant (tenant_id),
	CONSTRAINT fk_channels_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Usuarios finales (clientes)
CREATE TABLE IF NOT EXISTS end_users (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	channel_id CHAR(36) NOT NULL,
	chat_id VARCHAR(128) NOT NULL,
	name VARCHAR(128) NULL,
	username VARCHAR(128) NULL,
	locale VARCHAR(16) NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY uq_end_users_channel_chat (channel_id, chat_id),
	KEY idx_end_users_tenant (tenant_id),
	CONSTRAINT fk_end_users_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
	CONSTRAINT fk_end_users_channel FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Agentes humanos
CREATE TABLE IF NOT EXISTS agents (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	name VARCHAR(128) NOT NULL,
	email VARCHAR(128) NULL,
	is_active TINYINT(1) NOT NULL DEFAULT 1,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY uq_agents_email (email),
	KEY idx_agents_tenant (tenant_id),
	CONSTRAINT fk_agents_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Conversaciones
CREATE TABLE IF NOT EXISTS conversations (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	channel_id CHAR(36) NOT NULL,
	user_id CHAR(36) NOT NULL,
	ticket_id CHAR(36) NULL,
	status VARCHAR(32) NOT NULL DEFAULT 'open',
	opened_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	closed_at TIMESTAMP NULL DEFAULT NULL,
	PRIMARY KEY (id),
	KEY idx_conv_tenant (tenant_id),
	KEY idx_conv_user (user_id),
	KEY idx_conv_ticket (ticket_id),
	CONSTRAINT fk_conv_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
	CONSTRAINT fk_conv_channel FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
	CONSTRAINT fk_conv_user FOREIGN KEY (user_id) REFERENCES end_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Mensajes
CREATE TABLE IF NOT EXISTS messages (
	id CHAR(36) NOT NULL,
	conversation_id CHAR(36) NOT NULL,
	sender ENUM('user','agent','bot') NOT NULL,
	content TEXT NOT NULL,
	raw_payload JSON NULL,
	sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY idx_messages_conv_time (conversation_id, sent_at),
	CONSTRAINT fk_messages_conv FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tickets
CREATE TABLE IF NOT EXISTS tickets (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	user_id CHAR(36) NULL,
	subject VARCHAR(256) NULL,
	description TEXT NULL,
	status ENUM('open','pending','escalated','resolved','closed') NOT NULL DEFAULT 'open',
	priority ENUM('low','normal','high','urgent') NOT NULL DEFAULT 'normal',
	assigned_agent_id CHAR(36) NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY idx_tickets_tenant (tenant_id),
	KEY idx_tickets_status (status),
	KEY idx_tickets_assigned (assigned_agent_id),
	CONSTRAINT fk_tickets_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
	CONSTRAINT fk_tickets_user FOREIGN KEY (user_id) REFERENCES end_users(id) ON DELETE SET NULL,
	CONSTRAINT fk_tickets_agent FOREIGN KEY (assigned_agent_id) REFERENCES agents(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Eventos de ticket (auditoría)
CREATE TABLE IF NOT EXISTS ticket_events (
	id CHAR(36) NOT NULL,
	ticket_id CHAR(36) NOT NULL,
	event_type VARCHAR(64) NOT NULL,
	actor_type ENUM('user','agent','bot') NOT NULL,
	actor_id CHAR(36) NULL,
	metadata JSON NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY idx_ticket_events_ticket_time (ticket_id, created_at),
	CONSTRAINT fk_ticket_events_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tags
CREATE TABLE IF NOT EXISTS tags (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	name VARCHAR(64) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE KEY uq_tags_name_tenant (tenant_id, name),
	CONSTRAINT fk_tags_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ticket_tags (
	ticket_id CHAR(36) NOT NULL,
	tag_id CHAR(36) NOT NULL,
	PRIMARY KEY (ticket_id, tag_id),
	CONSTRAINT fk_ticket_tags_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
	CONSTRAINT fk_ticket_tags_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- FAQ
CREATE TABLE IF NOT EXISTS faq_categories (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	name VARCHAR(128) NOT NULL,
	slug VARCHAR(128) NULL,
	PRIMARY KEY (id),
	UNIQUE KEY uq_faq_cat_slug_tenant (tenant_id, slug),
	CONSTRAINT fk_faq_cat_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS faq_articles (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	category_id CHAR(36) NULL,
	question VARCHAR(512) NOT NULL,
	answer TEXT NOT NULL,
	keywords JSON NULL, -- lista de keywords en JSON
	is_active TINYINT(1) NOT NULL DEFAULT 1,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY idx_faq_articles_tenant (tenant_id),
	FULLTEXT KEY ftx_faq_question_answer (question, answer),
	CONSTRAINT fk_faq_articles_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
	CONSTRAINT fk_faq_articles_category FOREIGN KEY (category_id) REFERENCES faq_categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- NLU
CREATE TABLE IF NOT EXISTS nlu_intents (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	name VARCHAR(128) NOT NULL,
	description TEXT NULL,
	PRIMARY KEY (id),
	UNIQUE KEY uq_nlu_intents_name_tenant (tenant_id, name),
	CONSTRAINT fk_nlu_intents_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS nlu_synonyms (
	id CHAR(36) NOT NULL,
	intent_id CHAR(36) NOT NULL,
	value VARCHAR(256) NOT NULL,
	PRIMARY KEY (id),
	KEY idx_nlu_synonyms_intent (intent_id),
	CONSTRAINT fk_nlu_synonyms_intent FOREIGN KEY (intent_id) REFERENCES nlu_intents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS nlu_logs (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	user_id CHAR(36) NULL,
	message TEXT NOT NULL,
	detected_intent VARCHAR(128) NULL,
	confidence DECIMAL(6,5) NULL,
	metadata JSON NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY idx_nlu_logs_tenant_time (tenant_id, created_at),
	CONSTRAINT fk_nlu_logs_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
	CONSTRAINT fk_nlu_logs_user FOREIGN KEY (user_id) REFERENCES end_users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Versionado de reglas
CREATE TABLE IF NOT EXISTS config_versions (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	version INT NOT NULL,
	author VARCHAR(128) NULL,
	rules_yaml MEDIUMTEXT NOT NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY uq_config_versions (tenant_id, version),
	CONSTRAINT fk_config_versions_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Webhooks
CREATE TABLE IF NOT EXISTS webhooks (
	id CHAR(36) NOT NULL,
	tenant_id CHAR(36) NOT NULL,
	url TEXT NOT NULL,
	secret VARCHAR(256) NULL,
	event VARCHAR(64) NOT NULL,
	is_active TINYINT(1) NOT NULL DEFAULT 1,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY idx_webhooks_tenant (tenant_id),
	CONSTRAINT fk_webhooks_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS webhook_deliveries (
	id CHAR(36) NOT NULL,
	webhook_id CHAR(36) NOT NULL,
	payload JSON NOT NULL,
	status_code INT NULL,
	error TEXT NULL,
	delivered_at TIMESTAMP NULL,
	retries INT NOT NULL DEFAULT 0,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY idx_webhook_deliveries_webhook (webhook_id),
	CONSTRAINT fk_webhook_deliveries_webhook FOREIGN KEY (webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Vista de resumen de tickets
DROP VIEW IF EXISTS vw_ticket_overview;
CREATE VIEW vw_ticket_overview AS
SELECT t.id,
			 t.status,
			 t.priority,
			 t.created_at,
			 t.updated_at,
			 eu.name AS requester,
			 a.name  AS assigned_agent
FROM tickets t
LEFT JOIN end_users eu ON eu.id = t.user_id
LEFT JOIN agents a ON a.id = t.assigned_agent_id;

-- Notas
-- - Usa CHAR(36) para UUIDs generados por la app o por la función UUID().
-- - Asegura sql_mode estricto y zona horaria UTC.
-- - Considera particionado por rango en messages y ticket_events si el volumen crece.
