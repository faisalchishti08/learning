---
card: spring-session
gi: 12
slug: spring-session-jdbc-enablejdbchttpsession
title: "Spring Session JDBC (@EnableJdbcHttpSession)"
---

## 1. What it is

`spring-session-jdbc` is the relational-database-backed implementation of Spring Session, and `@EnableJdbcHttpSession` is the annotation that wires it up — composing the generic servlet plumbing (card 0005) with a `JdbcIndexedSessionRepository` bean, a default SQL schema (`SPRING_SESSION` and `SPRING_SESSION_ATTRIBUTES` tables), and its own internally scheduled cleanup task (card 0007) to handle expiration, since relational databases have no native key-TTL concept the way Redis does.

## 2. Why & when

Not every team wants to add Redis as a new piece of infrastructure just to get clustered sessions — many already run a relational database reliably, with existing backup, monitoring, and operational processes built around it. `@EnableJdbcHttpSession` lets that same database double as the session store, avoiding a new infrastructure dependency entirely, at the cost of slightly higher latency per session operation (a SQL round-trip versus Redis's in-memory speed) and needing an explicit scheduled cleanup task rather than Redis's native TTL.

Reach for `@EnableJdbcHttpSession` when:

- The team wants to avoid adding Redis as new infrastructure, and a relational database is already reliably operated.
- Session data benefits from living alongside other relational data for operational reasons — easier to include in existing database backup and disaster-recovery procedures than a separate Redis instance would be.
- Deciding between JDBC and Redis (card 0009) — prefer JDBC when minimizing new infrastructure and operational surface area matters more than raw read/write latency; prefer Redis when performance and native TTL-based expiration are priorities.

## 3. Core concept

Think of `@EnableRedisHttpSession` as renting a dedicated, purpose-built storage unit just for session data — fast to access, automatically empties itself on a schedule, but it's a new facility to manage. `@EnableJdbcHttpSession` is instead using a spare room in a warehouse the team already owns and operates — no new facility to set up or monitor separately, but it's a general-purpose space, not purpose-built for this, so someone (the scheduled cleanup task) has to actively walk through and clear out anything past its expiry date, since the warehouse itself has no self-emptying shelves the way the dedicated Redis unit does.

```java
@Configuration
@EnableJdbcHttpSession
public class JdbcSessionConfig {
    // Requires: a DataSource bean, a TransactionManager bean, and the
    // SPRING_SESSION / SPRING_SESSION_ATTRIBUTES schema applied to that database.
}
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JdbcIndexedSessionRepository stores sessions across two related tables and relies on its own scheduled cleanup task">
  <rect x="20" y="20" width="260" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">SPRING_SESSION</text>
  <text x="150" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">id, principal_name, expiry_time</text>
  <text x="150" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(one row per session)</text>

  <rect x="20" y="130" width="260" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="155" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">SPRING_SESSION_ATTRIBUTES</text>
  <text x="150" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">session_primary_id, attr_name, attr_bytes</text>
  <text x="150" y="190" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(one row per attribute)</text>

  <line x1="150" y1="90" x2="150" y2="125" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="380" y="80" width="220" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="490" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Scheduled cleanup task</text>
  <text x="490" y="122" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">DELETE WHERE expiry_time &lt; now</text>

  <line x1="280" y1="55" x2="375" y2="105" stroke="#f0883e" stroke-width="1.5"/>
</svg>

Session data is split across two normalized tables, and — unlike Redis — nothing removes expired rows except the library's own scheduled task.

## 5. Runnable example

The scenario: setting up JDBC-backed sessions with the default schema, growing to verify the built-in cleanup task is running correctly, and finally to add a database index tuned for the specific query patterns this application's session usage actually produces, since the default schema's indexes are reasonable general-purpose defaults, not necessarily optimal for every workload.

### Level 1 — Basic

```java
// JdbcSessionConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.session.jdbc.config.annotation.web.http.EnableJdbcHttpSession;

@Configuration
@EnableJdbcHttpSession
public class JdbcSessionConfig {
}
```

```properties
# application.properties
spring.datasource.url=jdbc:postgresql://localhost:5432/appdb
spring.sql.init.schema-locations=classpath:org/springframework/session/jdbc/schema-postgresql.sql
spring.sql.init.mode=always
```

**How to run:** with `spring-session-jdbc`, a `DataSource` configured, and the bundled schema script applied, start the app and make a request touching the session. Expected result: `SELECT * FROM SPRING_SESSION` shows a new row, and `SELECT * FROM SPRING_SESSION_ATTRIBUTES` shows one row per session attribute set — confirming the two-table structure is populated correctly.

### Level 2 — Intermediate

`JdbcIndexedSessionRepository` schedules its own cleanup task internally (`cleanupCron`, defaulting to a periodic sweep), but verifying it's genuinely running — not just configured — matters, since a misconfigured or silently failing cleanup task leads directly to unbounded table growth (card 0007).

```java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class JdbcCleanupHealthCheck {

    private final JdbcTemplate jdbcTemplate;
    private long lastExpiredCount = -1;

    public JdbcCleanupHealthCheck(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Scheduled(fixedRate = 120_000) // check every 2 minutes, offset from the library's own cleanup cadence
    public void checkCleanupIsWorking() {
        long expiredCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM SPRING_SESSION WHERE EXPIRE_TIME < ?",
                Long.class, System.currentTimeMillis());

        if (lastExpiredCount >= 0 && expiredCount >= lastExpiredCount && expiredCount > 100) {
            System.err.println("WARNING: expired session row count is not decreasing ("
                    + lastExpiredCount + " -> " + expiredCount + ") — cleanup task may not be running");
        }
        lastExpiredCount = expiredCount;
    }
}
```

**How to run:** enable `@EnableScheduling`, create many short-lived test sessions and let them expire, then watch this health check's log output over several cycles. Expected behavior under a correctly functioning setup: the expired-row count stays low and doesn't grow unboundedly, since the library's own cleanup task keeps deleting them. If `@EnableScheduling` were accidentally omitted (disabling the library's internal cleanup), the warning would fire as the count climbs steadily.

What changed: cleanup task health — normally an invisible internal detail — is now actively monitored, catching a misconfiguration that would otherwise manifest only weeks later as a slow, easy-to-miss storage growth problem.

### Level 3 — Advanced

The default schema's indexes support the query patterns Spring Session itself needs (lookup by session ID, by principal name, by expiry time for cleanup) — but a high-traffic application with a specific, unusual access pattern (say, extremely frequent `findByPrincipalName` calls against a very large sessions table) may benefit from an additional, purpose-built index beyond the defaults.

```sql
-- Verify the default schema's existing indexes first:
-- SPRING_SESSION_IX1: unique index on SESSION_ID
-- SPRING_SESSION_IX2: index on EXPIRE_TIME (supports cleanup queries)
-- SPRING_SESSION_IX3: index on PRINCIPAL_NAME (supports findByPrincipalName)

-- An example additional, workload-specific index for an application doing
-- frequent range queries on session creation time (e.g. an admin dashboard
-- showing "sessions created in the last hour"):
CREATE INDEX idx_spring_session_creation_time ON SPRING_SESSION (CREATION_TIME);
```

```java
import org.springframework.jdbc.core.JdbcTemplate;

public class RecentSessionsQuery {

    private final JdbcTemplate jdbcTemplate;

    public RecentSessionsQuery(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public int countSessionsCreatedInLastHour() {
        long oneHourAgo = System.currentTimeMillis() - 3_600_000;
        return jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM SPRING_SESSION WHERE CREATION_TIME > ?",
                Integer.class, oneHourAgo);
    }
}
```

**How to run:** run `EXPLAIN ANALYZE SELECT COUNT(*) FROM SPRING_SESSION WHERE CREATION_TIME > ...` before and after adding the custom index, against a table populated with a realistic volume of test session data. Expected observation: without the index, the database performs a full table scan; with it, the query plan uses the new index directly, and execution time drops noticeably as table size grows.

What changed and why it's production-flavored: this demonstrates that the bundled schema is a solid, general-purpose starting point, not necessarily the final word for every application's specific query patterns — a team building custom session-analytics features on top of the standard schema should feel free to add targeted indexes, exactly as they would for any other relational table serving an unusual access pattern.

## 6. Walkthrough

Tracing a session write and later cleanup under JDBC persistence, in execution order:

1. A request creates or modifies a session; `SessionRepositoryFilter` (card 0004) eventually calls `JdbcIndexedSessionRepository.save(...)`.
2. The repository executes an `INSERT` (for a new session) or `UPDATE` (for an existing one) against `SPRING_SESSION`, setting `EXPIRE_TIME` based on the current time plus `maxInactiveInterval`, and a `PRINCIPAL_NAME` column if the session has an associated authenticated principal (supporting indexed lookup, mirroring card 0003's capability but implemented relationally here).
3. For each session attribute, a corresponding row is written (or updated) in `SPRING_SESSION_ATTRIBUTES`, referencing the parent session's primary key — this normalized, one-row-per-attribute design is what lets individual attributes be updated without rewriting the entire session's data.
4. Both writes happen within a single database transaction (JDBC persistence requires a configured `PlatformTransactionManager`), ensuring the session row and its attribute rows never end up partially written relative to each other.
5. Independently of any request, the library's internally scheduled cleanup task (its cadence configured via `cleanupCron`) periodically executes a `DELETE` against `SPRING_SESSION` for rows whose `EXPIRE_TIME` has passed — cascading (via a foreign key or explicit companion delete, depending on the schema) to remove the corresponding `SPRING_SESSION_ATTRIBUTES` rows too, so attributes never outlive their parent session.
6. `JdbcCleanupHealthCheck` (Level 2) independently and periodically verifies this is actually happening, providing an operational safety net distinct from trusting the library's internal scheduling blindly.

```
save(session)
   |
BEGIN TRANSACTION
   INSERT/UPDATE SPRING_SESSION (id, principal_name, expiry_time, ...)
   INSERT/UPDATE SPRING_SESSION_ATTRIBUTES (session_id, attr_name, attr_bytes) x N
COMMIT
   |
(independently, on schedule) cleanupCron fires
   |
DELETE FROM SPRING_SESSION WHERE expiry_time < now
   -> cascades to remove matching SPRING_SESSION_ATTRIBUTES rows
```

## 7. Gotchas & takeaways

> `@EnableJdbcHttpSession`'s internal cleanup task requires task scheduling infrastructure to actually run — in most Spring Boot applications this works out of the box, but a from-scratch or heavily customized `TaskScheduler` setup can accidentally prevent it from firing, silently disabling cleanup (card 0007) with no startup error; Level 2's health check exists specifically to catch this.

- JDBC-backed sessions incur a real per-operation latency cost compared to Redis — a database round-trip (even to a fast, well-tuned relational database) is typically slower than an in-memory Redis operation; for latency-sensitive applications with very high session-touch rates, this difference is worth measuring before committing to JDBC over Redis.
- The default schema's `SPRING_SESSION_ATTRIBUTES` table stores each attribute as serialized bytes in a normalized, one-row-per-attribute design — sessions with a very large number of distinct attributes generate correspondingly more rows per session, which is worth being aware of when estimating table growth.
- Applying the bundled schema script (`schema-postgresql.sql`, `schema-mysql.sql`, and similar per-database variants) exactly as shipped is the safest path — deviating from it (renaming columns, changing types) without also providing custom row-mapping configuration risks the same kind of silent breakage covered for the authorization server's JDBC persistence.
- A custom, workload-specific index (Level 3) is a legitimate and often valuable addition on top of the default schema — treat the bundled schema as a solid foundation to build on, not an immutable contract that can never be extended with additional indexes tuned for a specific application's actual query patterns.
- When choosing between JDBC and Redis (card 0009) for a new application, let actual, measured requirements decide rather than defaulting reflexively to either — a low-to-moderate traffic internal tool with an already-well-operated database is a fine candidate for JDBC; a high-throughput, latency-sensitive public-facing application usually favors Redis.
