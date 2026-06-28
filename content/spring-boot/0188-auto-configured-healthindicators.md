---
card: spring-boot
gi: 188
slug: auto-configured-healthindicators
title: Auto-configured HealthIndicators
---

## 1. What it is

Spring Boot auto-configures `HealthIndicator` beans for the common infrastructure components it manages. Whenever a matching dependency is on the classpath and properly configured, the indicator is registered automatically — no code required. These indicators appear as components in the `/actuator/health` response.

Auto-configured indicators cover: relational databases (JDBC/JPA), MongoDB, Neo4j, Redis, RabbitMQ, Kafka, Elasticsearch, Cassandra, Couchbase, InfluxDB, LDAP, mail (SMTP), and JMS.

## 2. Why & when

The value is zero-configuration monitoring: as soon as you add `spring-boot-starter-data-redis`, a Redis `HealthIndicator` appears in `/actuator/health`. If Redis goes down, your health endpoint immediately reports `DOWN` for the `redis` component — with no extra code.

**When to configure auto-indicators:**
- Disable a specific indicator when the dependency is optional: `management.health.redis.enabled=false`.
- Adjust health check timeout for a slow external system.
- Add the dependency to the readiness health group while keeping it out of the liveness group.

**When to write a custom indicator instead:**
- The dependency has no auto-configured indicator (a third-party HTTP API, a proprietary SDK).
- You want richer details than the default check provides.

## 3. Core concept

Auto-configured `HealthIndicator`s and their triggering conditions:

| Component name | Auto-config class | Checks |
|---|---|---|
| `db` | `DataSourceHealthIndicatorAutoConfiguration` | `SELECT 1` (or driver-specific) |
| `mongo` | `MongoHealthIndicatorAutoConfiguration` | `db.runCommand({ ping: 1 })` |
| `neo4j` | `Neo4jHealthIndicatorAutoConfiguration` | `RETURN 1` Cypher |
| `redis` | `RedisHealthIndicatorAutoConfiguration` | `PING` command |
| `rabbit` | `RabbitHealthIndicatorAutoConfiguration` | admin API check |
| `kafka` | `KafkaHealthIndicatorAutoConfiguration` | listTopics timeout check |
| `elasticsearch` | `ElasticsearchHealthIndicatorAutoConfiguration` | cluster health API |
| `cassandra` | `CassandraHealthIndicatorAutoConfiguration` | `SELECT now() FROM system.local` |
| `mail` | `MailHealthIndicatorAutoConfiguration` | SMTP `EHLO` handshake |
| `diskSpace` | `DiskSpaceHealthIndicatorAutoConfiguration` | free disk vs. threshold |
| `ping` | `PingHealthIndicatorAutoConfiguration` | always UP (JVM alive check) |

All are enabled by default. Disable any with `management.health.<name>.enabled=false`.

Properties for customisation:
- `management.health.db.enabled=false`
- `management.health.diskspace.threshold=10MB` (note: `diskspace` not `disk-space`)
- `management.health.redis.timeout=2000ms`

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot auto-configures HealthIndicators based on classpath; each checks its dependency and contributes to /actuator/health">
  <!-- Classpath triggers (left) -->
  <rect x="10" y="20" width="180" height="168" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="40" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Classpath + Config</text>
  <text x="100" y="57" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starter-data-jpa      → db</text>
  <text x="100" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starter-data-redis    → redis</text>
  <text x="100" y="87" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starter-amqp          → rabbit</text>
  <text x="100" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starter-kafka         → kafka</text>
  <text x="100" y="117" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starter-data-mongodb  → mongo</text>
  <text x="100" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starter-mail          → mail</text>
  <text x="100" y="147" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starter-data-elasticsearch → es</text>
  <text x="100" y="162" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(always)              → diskSpace, ping</text>

  <!-- Arrow -->
  <line x1="193" y1="104" x2="258" y2="104" stroke="#6db33f" stroke-width="2" marker-end="url(#aia)"/>
  <text x="225" y="97" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">auto-config</text>

  <!-- Auto-registered indicators -->
  <rect x="263" y="20" width="185" height="168" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="355" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Registered Indicators</text>
  <text x="355" y="58" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">DataSourceHealthIndicator</text>
  <text x="355" y="74" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">RedisHealthIndicator</text>
  <text x="355" y="90" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">RabbitHealthIndicator</text>
  <text x="355" y="106" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">KafkaHealthIndicator</text>
  <text x="355" y="122" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">MongoHealthIndicator</text>
  <text x="355" y="138" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">MailHealthIndicator</text>
  <text x="355" y="154" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ElasticsearchHealthIndicator</text>
  <text x="355" y="170" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">DiskSpaceHealthIndicator</text>

  <!-- Arrow to health endpoint -->
  <line x1="451" y1="104" x2="515" y2="104" stroke="#6db33f" stroke-width="2" marker-end="url(#aia)"/>
  <text x="483" y="97" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">aggregate</text>

  <!-- /actuator/health -->
  <rect x="520" y="50" width="175" height="108" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="607" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">/actuator/health</text>
  <text x="520" y="87" fill="#6db33f" font-size="8" font-family="monospace">{ "status": "UP",</text>
  <text x="520" y="102" fill="#6db33f" font-size="8" font-family="monospace">  "components": {</text>
  <text x="520" y="117" fill="#6db33f" font-size="8" font-family="monospace">    "db":    "UP",</text>
  <text x="520" y="132" fill="#6db33f" font-size="8" font-family="monospace">    "redis": "DOWN",</text>
  <text x="520" y="147" fill="#6db33f" font-size="8" font-family="monospace">    "kafka": "UP"</text>
  <text x="520" y="154" fill="#6db33f" font-size="8" font-family="monospace">  }</text>

  <defs>
    <marker id="aia" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Spring Boot wires indicators automatically; the `components` map in the health response reflects exactly which starters are on the classpath.

## 5. Runnable example

```java
// AutoConfiguredIndicatorsDemo.java — demonstrates auto-configured health indicator simulation
// How to run: java AutoConfiguredIndicatorsDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add the matching starters; indicators appear in /actuator/health automatically

import java.util.*;

public class AutoConfiguredIndicatorsDemo {

    record IndicatorDef(String componentName, String starter, String checkDescription) {}
    record CheckResult(String status, Map<String, Object> details) {}

    // Simulated check outcomes
    static final Map<String, CheckResult> simulatedChecks = new LinkedHashMap<>(Map.of(
        "db",        new CheckResult("UP",   Map.of("database", "PostgreSQL 16", "validationQuery", "isValid()")),
        "redis",     new CheckResult("DOWN", Map.of("error", "Unable to connect to Redis at localhost:6379")),
        "rabbit",    new CheckResult("UP",   Map.of("version", "3.12.1")),
        "kafka",     new CheckResult("UP",   Map.of("numNodes", 3)),
        "diskSpace", new CheckResult("UP",   Map.of("total", "499GB", "free", "212GB", "threshold", "10MB"))
    ));

    static final List<IndicatorDef> autoConfigured = List.of(
        new IndicatorDef("db",        "spring-boot-starter-data-jpa",    "SELECT 1"),
        new IndicatorDef("mongo",     "spring-boot-starter-data-mongodb", "ping command"),
        new IndicatorDef("redis",     "spring-boot-starter-data-redis",  "PING"),
        new IndicatorDef("rabbit",    "spring-boot-starter-amqp",        "admin API"),
        new IndicatorDef("kafka",     "spring-boot-starter-kafka",       "listTopics"),
        new IndicatorDef("diskSpace", "(always active)",                 "free bytes > threshold"),
        new IndicatorDef("ping",      "(always active)",                 "always UP")
    );

    static String aggregate(Collection<CheckResult> results) {
        List<String> order = List.of("DOWN", "OUT_OF_SERVICE", "UNKNOWN", "UP");
        return results.stream()
                .map(CheckResult::status)
                .min(Comparator.comparingInt(order::indexOf))
                .orElse("UNKNOWN");
    }

    public static void main(String[] args) {
        System.out.println("=== Auto-configured HealthIndicators Demo ===\n");

        System.out.println("Available indicators and their triggering starters:");
        System.out.printf("  %-12s %-42s %s%n", "Component", "Starter", "Check");
        System.out.println("  " + "-".repeat(80));
        autoConfigured.forEach(d ->
            System.out.printf("  %-12s %-42s %s%n", d.componentName(), d.starter(), d.checkDescription()));

        System.out.println("\nSimulated /actuator/health response (db + redis + rabbit + kafka + diskSpace):");
        System.out.println("{");
        System.out.println("  \"status\": \"" + aggregate(simulatedChecks.values()) + "\",");
        System.out.println("  \"components\": {");
        simulatedChecks.forEach((name, result) ->
            System.out.printf("    \"%s\": { \"status\": \"%s\", \"details\": %s },%n",
                    name, result.status(), result.details()));
        System.out.println("  }");
        System.out.println("}");

        System.out.println("\n--- Disable specific indicators ---");
        System.out.println("management.health.redis.enabled=false     # ignore Redis in health");
        System.out.println("management.health.kafka.enabled=false     # ignore Kafka in health");

        System.out.println("\n--- Conditions report (why an indicator was/wasn't registered) ---");
        System.out.println("GET /actuator/conditions → check 'positiveMatches' for *HealthIndicatorAutoConfiguration");
    }
}
```

**How to run:** `java AutoConfiguredIndicatorsDemo.java`

## 6. Walkthrough

- The `IndicatorDef` table shows exactly which starter triggers which indicator — this mirrors the `@ConditionalOnBean` / `@ConditionalOnClass` conditions in each `*HealthIndicatorAutoConfiguration` class.
- **Simulation**: `redis=DOWN` with all others `UP` → aggregate status `DOWN` → the overall health is `DOWN`.
- **Disable pattern**: `management.health.redis.enabled=false` removes the `RedisHealthIndicator` bean. The `redis` key disappears from the `components` map entirely.
- **`/actuator/conditions`**: lists every auto-configuration condition. Filter for `HealthIndicatorAutoConfiguration` to diagnose why an expected indicator didn't register (usually missing dependency or bean).
- `ping` and `diskSpace` are always registered — `ping` is the minimal "is the JVM alive" indicator; `diskSpace` needs no dependency.

## 7. Gotchas & takeaways

> The `db` indicator runs a **validation query on every health check call** — on a heavily loaded system this adds DB queries. Consider using `management.health.db.enabled=false` and replacing with a custom indicator that checks a cheaper signal (e.g., connection pool active count from Micrometer).

> With **multiple DataSources**, each gets its own component name: `db`, `secondaryDb`, etc. Name them explicitly with `@Bean("secondaryDataSourceHealthIndicator")` to control the component names.

- Check indicator registration: `GET /actuator/beans` and search for `HealthIndicator` in the result — lists all registered health indicator beans.
- Composite indicator: use `CompositeHealthContributor.fromMap(Map.of("primary", ind1, "secondary", ind2))` to group multiple checks under one component name.
- Kafka `KafkaHealthIndicator` calls `AdminClient.listTopics()` — configure its timeout via `spring.kafka.admin.request-timeout-ms` to avoid long health check delays.
- Elasticsearch health indicator calls the `/_cluster/health` API — `red` cluster status maps to `DOWN`.
