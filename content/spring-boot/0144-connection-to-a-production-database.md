---
card: spring-boot
gi: 144
slug: connection-to-a-production-database
title: Connection to a production database
---

## 1. What it is

Connecting a Spring Boot application to a production database means providing the JDBC URL, credentials, and JDBC driver for a real external database (PostgreSQL, MySQL, Oracle, SQL Server, etc.). Spring Boot auto-configures a pooled `DataSource` from `spring.datasource.*` properties. Unlike embedded databases, production databases require the correct JDBC driver dependency, a reachable server, and externally managed credentials.

## 2. Why & when

Every production application eventually needs a persistent, external data store. You configure the production `DataSource` when:

- Moving from an in-memory H2 to PostgreSQL, MySQL, etc. for real data durability.
- Deploying to Kubernetes, EC2, or any cloud where the database runs as a separate service.
- Using a managed database service (AWS RDS, Cloud SQL, Azure Database).

Production database configuration also means thinking about security (no plaintext passwords in property files), reliability (connection pool tuning), and observability (pool metrics).

## 3. Core concept

Spring Boot needs three things:

1. **Driver** — JDBC driver JAR on the classpath (e.g. `org.postgresql:postgresql`).
2. **URL** — `spring.datasource.url=jdbc:postgresql://host:5432/dbname`
3. **Credentials** — `spring.datasource.username` and `spring.datasource.password`

The driver class is usually auto-detected from the URL prefix (`jdbc:postgresql:` → `org.postgresql.Driver`). Credentials should come from environment variables or a secrets manager, not hard-coded in `application.properties`.

Common production patterns:

```properties
# application-prod.properties
spring.datasource.url=${DB_URL}
spring.datasource.username=${DB_USER}
spring.datasource.password=${DB_PASSWORD}
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.connection-timeout=3000
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="103" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Spring Boot</text>
  <text x="95" y="120" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">HikariCP pool</text>
  <rect x="245" y="55" width="175" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="332" y="75" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Env vars / Secrets Mgr</text>
  <text x="332" y="93" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">DB_URL / DB_PASS</text>
  <rect x="245" y="125" width="175" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="332" y="147" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">JDBC Driver</text>
  <text x="332" y="164" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">org.postgresql / mysql…</text>
  <rect x="495" y="80" width="165" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="577" y="105" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">PostgreSQL</text>
  <text x="577" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">host:5432/db</text>
  <line x1="172" y1="110" x2="241" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#pd)"/>
  <line x1="172" y1="110" x2="241" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#pd)"/>
  <line x1="422" y1="110" x2="491" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pd2)"/>
  <defs>
    <marker id="pd" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="pd2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Spring Boot reads credentials from environment variables, uses the JDBC driver to open connections, and pools them via HikariCP.

## 5. Runnable example

```java
// ProductionDbApp.java — Spring Boot project with PostgreSQL
// pom.xml: spring-boot-starter-jdbc, org.postgresql:postgresql
//
// Set environment variables before running:
//   export DB_URL=jdbc:postgresql://localhost:5432/myapp
//   export DB_USER=appuser
//   export DB_PASS=s3cret
//
// application.properties:
//   spring.datasource.url=${DB_URL}
//   spring.datasource.username=${DB_USER}
//   spring.datasource.password=${DB_PASS}
//   spring.datasource.hikari.maximum-pool-size=10
//   spring.datasource.hikari.connection-timeout=3000
//   spring.datasource.hikari.validation-timeout=1000

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class ProductionDbApp {
    public static void main(String[] args) {
        SpringApplication.run(ProductionDbApp.class, args);
    }
}

@RestController
class HealthController {

    private final JdbcTemplate jdbc;

    HealthController(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    // Lightweight DB health check — used by load-balancer health probes
    @GetMapping("/db-ping")
    public String dbPing() {
        jdbc.queryForObject("SELECT 1", Integer.class);
        return "DB connection OK";
    }

    @GetMapping("/db-version")
    public String dbVersion() {
        return jdbc.queryForObject("SELECT version()", String.class);
    }
}
```

**How to run:**
1. Start PostgreSQL: `docker run -e POSTGRES_PASSWORD=s3cret -e POSTGRES_DB=myapp -p 5432:5432 postgres:16`
2. Set env vars: `export DB_URL=jdbc:postgresql://localhost:5432/myapp DB_USER=postgres DB_PASS=s3cret`
3. Start: `./mvnw spring-boot:run`
4. `curl http://localhost:8080/db-version` → PostgreSQL version string

## 6. Walkthrough

- `${DB_URL}` in `application.properties` is a property reference — Spring substitutes it from environment variables at startup. This keeps credentials out of source control.
- `spring-boot-starter-jdbc` + `org.postgresql:postgresql` (runtime scope) provide HikariCP and the PostgreSQL JDBC driver. Spring Boot detects the `jdbc:postgresql:` URL prefix and sets `spring.datasource.driver-class-name=org.postgresql.Driver` automatically.
- `spring.datasource.hikari.maximum-pool-size=10` limits open connections. For a busy app, tune this based on your database's `max_connections` setting and how many app instances run.
- `spring.datasource.hikari.connection-timeout=3000` means threads wait at most 3 seconds for a free connection before failing fast with an exception — better than hanging indefinitely under load.
- `jdbc.queryForObject("SELECT 1", Integer.class)` in `dbPing()` is a fast round-trip that validates the connection without touching application data — standard technique for health checks and load-balancer probes.
- Actuator's `/actuator/health` endpoint also checks the DataSource automatically when `spring-boot-starter-actuator` is on the classpath — no custom endpoint needed.

## 7. Gotchas & takeaways

> **Never hard-code passwords** in `application.properties` committed to source control. Use environment variables (`${DB_PASS}`), Spring Cloud Config, AWS Secrets Manager, or Kubernetes Secrets.

> Driver class detection from URL works for all major databases but fails for uncommon drivers. If auto-detection fails, set `spring.datasource.driver-class-name` explicitly.

- `spring.datasource.hikari.leak-detection-threshold=30000` logs a warning if a connection is held longer than 30 s — great for catching connection leaks in dev/staging.
- Use profile-specific properties (`application-prod.properties`) so dev uses H2 and prod uses PostgreSQL with no code changes.
- Cloud-native credential rotation: Hikari's `keepaliveTime` and `maxLifetime` ensure old connections are periodically refreshed, picking up rotated credentials via HikariCP `DataSourceProperties`.
- For MySQL, the URL typically adds `?useSSL=true&serverTimezone=UTC` — always check MySQL driver requirements.
- Spring Boot Actuator's `DataSourceHealthIndicator` runs `SELECT 1` (configurable via `spring.datasource.hikari.connection-test-query`) and reports `UP`/`DOWN` in `/actuator/health`.
