# Base de datos MySQL para ClientCare Bot

Esquema profesional para MySQL 8.0, con enfoque multi-tenant, auditabilidad y escalabilidad.

## Requisitos
- MySQL 8.0+
- Motor InnoDB
- Charset y collation: utf8mb4 / utf8mb4_unicode_ci
- sql_mode estricto (ej. `STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION`)

## Aplicación del esquema

```sql
-- Crear base de datos (opcional)
CREATE DATABASE IF NOT EXISTS clientcare
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
USE clientcare;

-- (Opcional) función UUID si la app no lo genera
-- CREATE FUNCTION uuid_v4() RETURNS CHAR(36) DETERMINISTIC RETURN UUID();

-- Ejecutar el esquema
SOURCE docs/sql/schema.sql;
```

## Decisiones de diseño clave
- Multi-tenant por `tenant_id` en tablas principales.
- Identificadores `CHAR(36)` (UUID) para evitar colisiones y facilitar sharding.
- Enums nativos de MySQL para `status`, `priority`, `sender` y `channel`.
- Mensajería y conversaciones separadas para trazabilidad.
- Auditoría con `ticket_events` y versionado de reglas con `config_versions`.
- Búsquedas: índice FULLTEXT en FAQ (`question`, `answer`); `keywords` en JSON.

## Consultas típicas

- Tickets abiertos por agente:
```sql
SELECT * FROM tickets
WHERE assigned_agent_id = ? AND status IN ('open','pending')
ORDER BY FIELD(priority,'urgent','high','normal','low'), created_at ASC;
```

- Últimos mensajes de una conversación:
```sql
SELECT * FROM messages
WHERE conversation_id = ?
ORDER BY sent_at DESC
LIMIT 50;
```

- Búsqueda de FAQ por término:
```sql
SELECT * FROM faq_articles
WHERE is_active = 1 AND MATCH(question, answer) AGAINST (? IN NATURAL LANGUAGE MODE)
LIMIT 20;
```

- Resumen de tickets:
```sql
SELECT * FROM vw_ticket_overview
ORDER BY updated_at DESC
LIMIT 100;
```

## Siguientes pasos recomendados
- Particionado por rango (por fecha) en `messages` y `ticket_events` si hay alto volumen.
- Purga y archivado programado de `nlu_logs` y `webhook_deliveries`.
- Índices adicionales basados en consultas reales (EXPLAIN ANALYZE).
- Implementar RLS en capa de app (MySQL no soporta RLS nativo).
