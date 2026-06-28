---
card: spring-boot
gi: 255
slug: configuring-for-production
title: Configuring for production
---

## 1. What it is

**Configuring for production** means applying the set of Spring Boot settings — across `application.properties`, JVM flags, Actuator, logging, and security — that turn a development-mode app into a hardened, observable, reliable service.

Spring Boot's defaults are developer-friendly (verbose errors, all Actuator endpoints exposed, auto-DDL enabled). Production defaults are different: minimal error detail exposed to clients, health + metrics endpoints only, schema management off, graceful shutdown on, structured logging, and externalized secrets.

The full production checklist touches:

1. **Security** — TLS, no sensitive data in logs, restricted Actuator.
2. **Resilience** — graceful shutdown, connection pool sizing, timeout config.
3. **Observability** — structured logs, metrics, distributed tracing.
4. **Configuration management** — no secrets in JARs, environment-specific overrides.
5. **JVM tuning** — heap size, GC selection, `XX:+ExitOnOutOfMemoryError`.

## 2. Why & when

The default Spring Boot configuration is wrong for production in several ways:

- `spring.jpa.hibernate.ddl-auto=create-drop` is the *test* default — production databases must not be dropped on restart.
- `management.endpoints.web.exposure.include=*` exposes heap dumps, thread dumps, and env details to anyone who can reach Actuator.
- `server.error.include-stacktrace=always` leaks implementation details in HTTP error responses.
- Logging is line-based by default; log aggregation tools (Datadog, Splunk, CloudWatch) work better with JSON.

Apply production configuration at **deploy time** via environment variables or an externalized config file — never by baking production secrets into the JAR.

## 3. Core concept

Think of Spring Boot's default config as a **car with the doors unlocked and the headlights on**. Fine in a garage (development), but you need to lock the doors, turn on the seat belt warning, and switch to the right fuel before driving on the highway (production).

Spring Boot's config loading order makes externalisation easy:
1. `application.properties` inside JAR (base defaults).
2. `application-prod.properties` on the filesystem (overrides when `SPRING_PROFILES_ACTIVE=prod`).
3. Environment variables (`SPRING_DATASOURCE_URL` overrides `spring.datasource.url`).
4. Command-line arguments (`--server.port=9090`).

Environment variables have the highest practical precedence, so platforms (Kubernetes Secrets, AWS Parameter Store, CF env vars) can inject values without touching the JAR.

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Production configuration layers from JAR defaults to environment variable overrides">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Stacked layers (lower = applied first = lower precedence) -->
  <rect x="100" y="200" width="500" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="218" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">application.properties (inside JAR) — base defaults</text>
  <text x="630" y="218" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">lowest</text>

  <rect x="100" y="158" width="500" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="350" y="176" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">application-prod.properties (filesystem) — env overrides</text>

  <rect x="100" y="116" width="500" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="134" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Environment variables — SPRING_DATASOURCE_URL etc.</text>

  <rect x="100" y="74" width="500" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="92" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">CLI args / Secrets Manager — final override</text>
  <text x="630" y="92" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">highest</text>

  <!-- Upward arrow = precedence -->
  <line x1="60" y1="220" x2="60" y2="80" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>
  <text x="35" y="155" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" transform="rotate(-90 35 155)">precedence</text>

  <text x="350" y="255" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Secrets come from environment — never baked into the JAR</text>
</svg>

Higher layers override lower ones; environment variables beat JAR-embedded properties, making secrets injectable without rebuilding.

## 5. Runnable example

```java
// ProductionConfigDemo.java — run with: java ProductionConfigDemo.java
// Prints the complete production application.properties checklist
// with explanations for each setting.

public class ProductionConfigDemo {

    record Setting(String key, String value, String why) {}

    public static void main(String[] args) {
        System.out.println("=== Spring Boot Production Configuration Checklist ===\n");

        Setting[][] sections = {
            {   // Security
                new Setting("server.error.include-stacktrace", "never",
                    "Don't leak stack traces to HTTP clients"),
                new Setting("server.error.include-message", "never",
                    "Don't expose exception messages in error responses"),
                new Setting("management.endpoints.web.exposure.include", "health,info,metrics,prometheus",
                    "Never expose env, heapdump, or mappings publicly"),
                new Setting("management.endpoint.health.show-details", "when-authorized",
                    "Full health details only for authenticated ops users"),
                new Setting("server.ssl.enabled", "true  # + keystore config",
                    "TLS in production; terminate at load balancer or in app"),
            },
            {   // Resilience
                new Setting("server.shutdown", "graceful",
                    "Complete in-flight requests before exit"),
                new Setting("spring.lifecycle.timeout-per-shutdown-phase", "30s",
                    "Wait 30s per phase before force-closing"),
                new Setting("spring.datasource.hikari.maximum-pool-size", "20",
                    "Size pool to match DB max connections / number of instances"),
                new Setting("spring.datasource.hikari.connection-timeout", "3000",
                    "Fail fast (3s) rather than queuing indefinitely"),
                new Setting("spring.jpa.open-in-view", "false",
                    "Avoid holding DB connections across view rendering"),
            },
            {   // Database safety
                new Setting("spring.jpa.hibernate.ddl-auto", "validate",
                    "Never drop/create schema in production — use Flyway/Liquibase"),
                new Setting("spring.flyway.enabled", "true",
                    "Use Flyway for safe versioned schema migrations"),
            },
            {   // Observability
                new Setting("logging.structured.format.console", "ecs",
                    "JSON/ECS logs for log aggregators (Datadog, Splunk, etc.)"),
                new Setting("management.tracing.sampling.probability", "0.1",
                    "10% trace sampling — adjust per traffic volume"),
                new Setting("management.metrics.export.prometheus.enabled", "true",
                    "Prometheus scrape endpoint for Grafana"),
            },
            {   // JVM flags (set in ExecStart/JAVA_OPTS, not application.properties)
                new Setting("-Xmx512m", "(JVM flag)",
                    "Cap heap to prevent OOM kills by the OS"),
                new Setting("-XX:+ExitOnOutOfMemoryError", "(JVM flag)",
                    "Crash cleanly on OOM rather than limping in degraded state"),
                new Setting("-XX:+UseG1GC", "(JVM flag)",
                    "G1GC balances throughput and pause time for typical web apps"),
            },
        };

        String[] headers = {"Security", "Resilience", "Database Safety", "Observability", "JVM Flags"};
        for (int s = 0; s < sections.length; s++) {
            System.out.println("--- " + headers[s] + " ---");
            for (Setting setting : sections[s]) {
                System.out.printf("  %-55s = %-35s  # %s%n",
                    setting.key(), setting.value(), setting.why());
            }
            System.out.println();
        }
    }
}
```

**How to run:** `java ProductionConfigDemo.java`

## 6. Walkthrough

- **`server.error.include-stacktrace=never`** — prevents the default Spring error response (`/error`) from including the Java stack trace in the JSON body. Attackers use stack traces to identify library versions and known CVEs. Set to `never` in production; use centralized logging to capture full details server-side.
- **`management.endpoints.web.exposure.include=health,info,metrics,prometheus`** — the default `*` exposes `heapdump`, `threaddump`, `env` (which prints all properties including secrets), and `beans`. Restrict to operational endpoints only. Secure even those behind a firewall or Spring Security rule.
- **`spring.datasource.hikari.connection-timeout=3000`** — HikariCP's default connection-acquisition timeout is 30 seconds. If the DB is down or overloaded, 30 s waits queue up threads and cause cascading failures. 3 s fails fast and lets circuit breakers act.
- **`spring.jpa.hibernate.ddl-auto=validate`** — `validate` checks that the entity model matches the schema without modifying it. `create-drop` (test default) drops and recreates the schema on every startup. In production, use Flyway (`spring-boot-starter-data-jpa` + `spring-boot-starter-flyway`) for all schema changes.
- **`-XX:+ExitOnOutOfMemoryError`** — a JVM flag (not a Spring property). When heap is exhausted, the default JVM behaviour is to throw `OutOfMemoryError` from the thread that triggered it; the app often continues in a half-alive state, silently dropping requests. `ExitOnOutOfMemoryError` causes a clean exit; the process manager (systemd, Kubernetes) restarts it.

## 7. Gotchas & takeaways

> **`spring.jpa.open-in-view=true` (the default) holds a database connection for the entire HTTP request lifecycle, including view rendering.** On high-traffic apps this exhausts the connection pool. Set it to `false` — it forces you to load all data in the service layer before returning to the controller, which is correct design anyway.

> **Structured logging (`logging.structured.format.console=ecs`) changes the log format from human-readable lines to JSON objects.** Your local dev console looks ugly but your log aggregator will correctly parse fields, enabling time-range queries, error-rate alerts, and trace correlation. Use a development profile (`application-dev.properties`) that overrides back to plain text locally.

- Use `SPRING_PROFILES_ACTIVE=prod` as an environment variable — no need to change the JAR.
- Store secrets (DB passwords, API keys) in a secrets manager and inject them as environment variables — `SPRING_DATASOURCE_PASSWORD` overrides `spring.datasource.password` automatically.
- Enable health probes: `management.endpoint.health.probes.enabled=true` for Kubernetes readiness/liveness integration.
- Tune `hikari.maximum-pool-size` = `(DB max_connections) / (number of app instances)` — avoid overwhelming the DB.
- Run `mvn spring-boot:run -Dspring-boot.run.profiles=prod` locally to verify the prod config before deploying.
