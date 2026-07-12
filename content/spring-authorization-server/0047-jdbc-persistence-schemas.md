---
card: spring-authorization-server
gi: 47
slug: jdbc-persistence-schemas
title: "JDBC persistence schemas"
---

## 1. What it is

Spring Authorization Server ships JDBC implementations of its three core persistence interfaces — `JdbcRegisteredClientRepository` (card 0011), `JdbcOAuth2AuthorizationService` (card 0017), and `JdbcOAuth2AuthorizationConsentService` (card 0018) — along with default SQL schema scripts (`oauth2-registered-client-schema.sql`, `oauth2-authorization-schema.sql`, `oauth2-authorization-consent-schema.sql`) that define the exact tables and columns these implementations expect.

## 2. Why & when

In-memory implementations (the default for a quick start) lose all registered clients and active authorizations on every restart, and don't work at all across multiple server instances — the second instance never sees clients or authorizations created via the first. JDBC persistence solves both problems by backing everything with a real, shared database, but it comes with a hard constraint: the library's `JdbcRegisteredClientRepository` and friends do direct JDBC-level SQL against very specific table and column names, so getting the schema right (or deliberately customizing the row mappers to match a different schema) is not optional.

Reach for JDBC persistence when:

- Deploying more than one instance of the authorization server behind a load balancer — every instance needs to see the same registered clients and the same in-flight authorizations.
- Needing registered clients and authorizations to survive a server restart or redeploy, which in-memory implementations never do.
- Deciding between the default schema and a custom one — the default scripts are the fastest path and are what most deployments should start with; only diverge (with custom `RowMapper`/`Function<RegisteredClient, List<SqlParameterValue>>` implementations) when integrating with an existing database schema that can't be changed to match.

## 3. Core concept

Think of the default schema scripts as a prefabricated warehouse shelving unit that arrives with fixed slot dimensions — the `JdbcRegisteredClientRepository` (the warehouse robot that stocks and retrieves items) is built to expect items sized exactly for those slots. Run the provided SQL scripts unchanged, and the robot works immediately. Try to put the same robot in front of *your own* differently-sized shelving (an existing, pre-existing database schema) without reconfiguring it, and it'll either fail to find what it's looking for or, worse, silently write into the wrong slot — which is exactly why customizing the schema requires customizing the row mappers in lockstep.

```sql
-- oauth2_registered_client (abbreviated)
CREATE TABLE oauth2_registered_client (
    id varchar(100) NOT NULL,
    client_id varchar(100) NOT NULL,
    client_secret varchar(200),
    client_authentication_methods varchar(1000) NOT NULL,
    authorization_grant_types varchar(1000) NOT NULL,
    redirect_uris varchar(1000),
    scopes varchar(1000) NOT NULL,
    ...
    PRIMARY KEY (id)
);
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple authorization server instances share one database via the JDBC repository implementations">
  <rect x="20" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="48" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Server instance 1</text>

  <rect x="20" y="90" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="118" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Server instance 2</text>

  <rect x="20" y="160" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="188" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Server instance 3</text>

  <rect x="380" y="70" width="220" height="100" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Shared database</text>
  <text x="490" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">oauth2_registered_client</text>
  <text x="490" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">oauth2_authorization</text>
  <text x="490" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">oauth2_authorization_consent</text>

  <line x1="160" y1="43" x2="375" y2="100" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="160" y1="113" x2="375" y2="115" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="160" y1="183" x2="375" y2="130" stroke="#3fb950" stroke-width="1.5"/>
</svg>

Any instance can issue a code and any other instance can redeem it — the database, not any one server process, is the source of truth.

## 5. Runnable example

The scenario: wiring `JdbcRegisteredClientRepository` and `JdbcOAuth2AuthorizationService` with the default schema, growing to verify the schema is applied correctly at startup, and finally to add a custom column and a matching row-mapper extension for tenant-scoped client isolation.

### Level 1 — Basic

```java
// JdbcPersistenceConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.oauth2.server.authorization.client.JdbcRegisteredClientRepository;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClientRepository;
import org.springframework.security.oauth2.server.authorization.JdbcOAuth2AuthorizationService;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationService;

@Configuration
public class JdbcPersistenceConfig {

    @Bean
    public RegisteredClientRepository registeredClientRepository(JdbcTemplate jdbcTemplate) {
        return new JdbcRegisteredClientRepository(jdbcTemplate);
    }

    @Bean
    public OAuth2AuthorizationService authorizationService(
            JdbcTemplate jdbcTemplate, RegisteredClientRepository registeredClientRepository) {
        return new JdbcOAuth2AuthorizationService(jdbcTemplate, registeredClientRepository);
    }
}
```

```properties
# application.properties
spring.datasource.url=jdbc:postgresql://localhost:5432/authserver
spring.sql.init.schema-locations=classpath:org/springframework/security/oauth2/server/authorization/oauth2-registered-client-schema.sql,classpath:org/springframework/security/oauth2/server/authorization/oauth2-authorization-schema.sql,classpath:org/springframework/security/oauth2/server/authorization/oauth2-authorization-consent-schema.sql
spring.sql.init.mode=always
```

**How to run:** with a running PostgreSQL instance and these properties, start the Boot app — the default schema scripts (bundled inside the `spring-security-oauth2-authorization-server` jar) run automatically. Register a client, restart the app, and query it again: expect it to still exist, unlike an in-memory repository (card 0011).

### Level 2 — Intermediate

Silently starting with a missing or malformed table is a common deployment mistake — production adds an explicit startup check that fails fast with a clear message rather than letting the first real request produce a cryptic SQL error.

```java
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
public class SchemaVerifier {

    private final JdbcTemplate jdbcTemplate;

    public SchemaVerifier(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void verifySchema() {
        String[] requiredTables = {"oauth2_registered_client", "oauth2_authorization", "oauth2_authorization_consent"};
        for (String table : requiredTables) {
            Integer count = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                    Integer.class, table);
            if (count == null || count == 0) {
                throw new IllegalStateException(
                        "Required table '" + table + "' is missing — has the OAuth2 schema been applied?");
            }
        }
    }
}
```

**How to run:** start the app against a database missing one of the required tables (e.g. skip the schema init step). Expected behavior: the application fails to start with a clear `IllegalStateException` naming the missing table, instead of starting successfully and only failing later, confusingly, on the first real client registration attempt.

What changed: schema problems are now caught at deploy time, with a message that names the actual missing piece — turning a production incident during the first real request into a failed deployment that's caught in CI or staging instead.

### Level 3 — Advanced

A genuinely custom requirement — say, associating each registered client with a `tenant_id` for a multi-tenant deployment — requires both an `ALTER TABLE` migration and a custom `RegisteredClientRepository` wrapping the JDBC one, since `JdbcRegisteredClientRepository` itself has no concept of tenants.

```sql
-- V2__add_tenant_id.sql (a Flyway-style migration, run after the base schema)
ALTER TABLE oauth2_registered_client ADD COLUMN tenant_id varchar(100);
CREATE INDEX idx_registered_client_tenant ON oauth2_registered_client (tenant_id);
```

```java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.oauth2.server.authorization.client.JdbcRegisteredClientRepository;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClientRepository;

public class TenantAwareRegisteredClientRepository implements RegisteredClientRepository {

    private final JdbcRegisteredClientRepository delegate;
    private final JdbcTemplate jdbcTemplate;

    public TenantAwareRegisteredClientRepository(JdbcRegisteredClientRepository delegate, JdbcTemplate jdbcTemplate) {
        this.delegate = delegate;
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public void save(RegisteredClient registeredClient) {
        delegate.save(registeredClient); // base columns via the library's own logic
    }

    public void assignTenant(String registeredClientId, String tenantId) {
        jdbcTemplate.update(
                "UPDATE oauth2_registered_client SET tenant_id = ? WHERE id = ?",
                tenantId, registeredClientId);
    }

    public java.util.List<String> findClientIdsForTenant(String tenantId) {
        return jdbcTemplate.queryForList(
                "SELECT client_id FROM oauth2_registered_client WHERE tenant_id = ?",
                String.class, tenantId);
    }

    @Override
    public RegisteredClient findById(String id) { return delegate.findById(id); }

    @Override
    public RegisteredClient findByClientId(String clientId) { return delegate.findByClientId(clientId); }
}
```

**How to run:** apply the migration, save a client via the base `save(...)`, then call `assignTenant(clientId, "tenant-42")`. Query `findClientIdsForTenant("tenant-42")`: expect the client's `client_id` returned. Standard OAuth2 flows against that client continue to work unchanged, since `save`/`findById`/`findByClientId` still delegate to the untouched `JdbcRegisteredClientRepository`.

What changed and why it's production-flavored: the base schema and repository remain fully intact and library-supported, while tenant scoping is layered on top as an additive column and a thin wrapper — avoiding the far riskier path of forking or hand-rewriting the library's own SQL, which would need to be kept in sync with every future library upgrade.

## 6. Walkthrough

Tracing a client registration and lookup against JDBC persistence, in execution order:

1. On application startup, `SchemaVerifier` (Level 2) confirms all three required tables exist, failing fast if the schema wasn't applied.
2. An administrator (or the dynamic registration endpoint, card 0034) calls `registeredClientRepository.save(newClient)`.
3. `JdbcRegisteredClientRepository.save(...)` serializes the `RegisteredClient`'s fields — including collection-valued fields like `scopes` and `redirectUris`, which it flattens into delimited strings — and executes an `INSERT` (or `UPDATE`, if the ID already exists) against `oauth2_registered_client`.
4. `TenantAwareRegisteredClientRepository.assignTenant(...)` (Level 3) runs a separate, direct `UPDATE` to populate the custom `tenant_id` column the base library implementation doesn't know about.
5. Later, a different server instance behind the same load balancer receives an authorization request for this client's `client_id`.
6. That instance's own `JdbcRegisteredClientRepository.findByClientId(...)` queries the same shared table, reconstructing a `RegisteredClient` object identical to the one saved by the first instance — the two server processes never communicated directly; the database is the sole shared state.
7. The request proceeds through the normal authorization flow (card 0026) exactly as if it had been registered on the same instance now serving the request.

```
Instance 1: save(client) -> INSERT INTO oauth2_registered_client ...
                          -> UPDATE ... SET tenant_id = 'tenant-42' WHERE id = ...
                                        |
                                  shared database
                                        |
Instance 2: findByClientId("task-tracker") -> SELECT ... FROM oauth2_registered_client WHERE client_id = ?
                                            -> reconstructs identical RegisteredClient
```

## 7. Gotchas & takeaways

> The default JDBC implementations do direct SQL against exact table and column names — renaming a column, changing a type, or dropping a column they expect (without also providing a corresponding custom `RowMapper`) breaks them silently or with an opaque SQL exception, not a clear library-level error. Treat the default schema as a contract, not a suggestion, unless fully committing to the custom row-mapper path.

- Always run schema verification (Level 2) or an equivalent startup check in any environment where the schema is managed separately from the application (a DBA-controlled database, a shared staging environment) — the failure mode of a missing table is much easier to diagnose at startup than mid-request.
- Multi-instance deployments require JDBC (or another shared store) persistence for *all three* repositories consistently — mixing an in-memory `OAuth2AuthorizationConsentService` with a JDBC `RegisteredClientRepository`, for instance, means consent state silently doesn't survive restarts or replicate across instances even though clients do.
- Custom columns (Level 3) should be added additively (new nullable columns, new indexes) rather than by modifying or removing any column the base `JdbcRegisteredClientRepository`/`JdbcOAuth2AuthorizationService` implementations read or write — this keeps library upgrades safe, since the base implementations' expectations haven't changed underneath them.
- `oauth2_authorization` rows can grow large — it stores the full authorization code, access token, refresh token, and their metadata together per row; plan storage and retention (a scheduled cleanup job for expired authorizations) accordingly rather than letting the table grow unbounded.
- When debugging a JDBC persistence issue, check the actual SQL being executed (enable JDBC statement logging) before assuming application logic is wrong — a surprising number of these issues turn out to be a schema drift between what the library expects and what the database actually has.
