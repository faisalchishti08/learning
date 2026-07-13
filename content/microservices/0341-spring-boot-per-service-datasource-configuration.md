---
card: microservices
gi: 341
slug: spring-boot-per-service-datasource-configuration
title: "Spring Boot per-service datasource configuration"
---

## 1. What it is

**Per-service datasource configuration** in Spring Boot means each microservice's `application.yml` (or `application.properties`) declares connection details — URL, credentials, driver, pool size — pointing exclusively at that one service's own private database, with no service's configuration ever referencing another service's datasource. Spring Boot's autoconfiguration picks up `spring.datasource.*` properties and wires a connection pool (typically HikariCP) and, for JPA-based services, an `EntityManagerFactory`, entirely from that one service's own configuration file.

## 2. Why & when

[Database per service](0304-database-per-service-pattern.md) is an architectural principle; per-service datasource configuration is how it's actually enforced in a Spring Boot codebase. If every service's `application.yml` only ever contains connection details for its own database, there is no way for that service's code to accidentally query another service's tables directly — the coupling simply isn't wired up at the configuration layer. This is a cheap, mechanical safeguard for a principle that could otherwise be violated by a single stray connection string.

Configure a distinct datasource per service, using environment-specific values (often injected via environment variables or a config server, not hardcoded) so the same service's Docker image can run against different databases in different environments without a code change. Pay particular attention to connection pool sizing (`spring.datasource.hikari.maximum-pool-size`) per service, since each service's own database has its own connection limits, and an oversized pool in one service can exhaust a shared database server's total connection budget even though the databases are logically separate.

## 3. Core concept

Spring Boot's `DataSourceAutoConfiguration` reads `spring.datasource.url`, `spring.datasource.username`, `spring.datasource.password`, and related properties from that service's own configuration and builds a connection pool from them — entirely local to the service's own process and configuration file, with no cross-service reference possible through this mechanism.

```yaml
# order-service/src/main/resources/application.yml
spring:
  datasource:
    url: jdbc:postgresql://order-db:5432/orders
    username: ${ORDER_DB_USER}
    password: ${ORDER_DB_PASSWORD}
    hikari:
      maximum-pool-size: 10
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="order-service's application.yml points only at order-db; payment-service's application.yml points only at payment-db; neither configuration file references the other service's database">
  <rect x="20" y="20" width="260" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">order-service application.yml</text>
  <text x="150" y="60" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">spring.datasource.url = order-db</text>

  <rect x="360" y="20" width="260" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="490" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">payment-service application.yml</text>
  <text x="490" y="60" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">spring.datasource.url = payment-db</text>

  <line x1="150" y1="80" x2="150" y2="120" stroke="#6db33f" marker-end="url(#a341)"/>
  <rect x="60" y="120" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="142" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-db (private)</text>

  <line x1="490" y1="80" x2="490" y2="120" stroke="#79c0ff" marker-end="url(#a341b)"/>
  <rect x="400" y="120" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="490" y="142" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">payment-db (private)</text>

  <defs>
    <marker id="a341" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="a341b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Each service's own configuration file wires its connection pool to exactly one, private database — no cross-service reference exists in either file.

## 5. Runnable example

Scenario: two Java programs simulating order-service and payment-service each reading their own configuration and building their own isolated connection pool, first shown naively sharing one pool (violating isolation), then fixed with separate per-service pools, and finally extended to size each pool appropriately for its own service's load.

### Level 1 — Basic

```java
// File: SharedPoolViolatesIsolation.java -- BOTH "services" use the SAME
// connection pool / config -- violating database-per-service isolation.
import java.util.*;

public class SharedPoolViolatesIsolation {
    record DataSourceConfig(String url, int maxPoolSize) {}
    static DataSourceConfig sharedConfig = new DataSourceConfig("jdbc:postgresql://shared-db:5432/everything", 20);

    static void connectAsOrderService() { System.out.println("order-service connecting via: " + sharedConfig.url()); }
    static void connectAsPaymentService() { System.out.println("payment-service connecting via: " + sharedConfig.url() + " -- SAME database as order-service!"); }

    public static void main(String[] args) {
        connectAsOrderService();
        connectAsPaymentService();
        System.out.println("Both services share ONE datasource config -- nothing stops either from querying the other's tables.");
    }
}
```

How to run: `java SharedPoolViolatesIsolation.java`

Both simulated services read from the identical `sharedConfig`, pointing at the same database. Even if the application code today only queries its "own" tables, nothing in this configuration prevents either service from reaching into the other's tables — the isolation [database per service](0304-database-per-service-pattern.md) calls for exists only by convention, not by configuration.

### Level 2 — Intermediate

```java
// File: PerServiceDataSourceConfig.java -- each service reads its OWN
// configuration, pointing at its OWN database; there is no shared config
// object at all.
import java.util.*;

public class PerServiceDataSourceConfig {
    record DataSourceConfig(String url, String username, int maxPoolSize) {}

    // Simulates order-service's OWN application.yml being loaded.
    static DataSourceConfig loadOrderServiceConfig() {
        return new DataSourceConfig("jdbc:postgresql://order-db:5432/orders", "order_svc_user", 10);
    }

    // Simulates payment-service's OWN, ENTIRELY SEPARATE application.yml.
    static DataSourceConfig loadPaymentServiceConfig() {
        return new DataSourceConfig("jdbc:postgresql://payment-db:5432/payments", "payment_svc_user", 10);
    }

    public static void main(String[] args) {
        DataSourceConfig orderConfig = loadOrderServiceConfig();
        DataSourceConfig paymentConfig = loadPaymentServiceConfig();

        System.out.println("order-service datasource: " + orderConfig);
        System.out.println("payment-service datasource: " + paymentConfig);
        System.out.println("Two ENTIRELY separate configs -- no code path could ever cross-connect them.");
    }
}
```

How to run: `java PerServiceDataSourceConfig.java`

`loadOrderServiceConfig` and `loadPaymentServiceConfig` are independent methods returning independent `DataSourceConfig` values, standing in for each service reading its own, separate `application.yml`. There is no shared object or shared code path linking the two — the isolation is structural, not just a matter of application-level discipline.

### Level 3 — Advanced

```java
// File: SizedPoolsPerServiceLoad.java -- each service's pool is sized
// based on ITS OWN expected concurrency, not a one-size-fits-all number;
// an oversized pool from a high-traffic service could otherwise exhaust
// the database server's total connection budget even with separate databases.
import java.util.*;

public class SizedPoolsPerServiceLoad {
    record DataSourceConfig(String url, int maxPoolSize, int expectedConcurrentRequests) {}

    static DataSourceConfig loadOrderServiceConfig() { // high traffic -- needs a larger pool
        return new DataSourceConfig("jdbc:postgresql://order-db:5432/orders", 30, 25);
    }
    static DataSourceConfig loadAuditServiceConfig() { // low traffic, occasional batch writes -- small pool is fine
        return new DataSourceConfig("jdbc:postgresql://audit-db:5432/audit", 5, 2);
    }

    static void validatePoolSizing(String serviceName, DataSourceConfig config) {
        if (config.maxPoolSize() < config.expectedConcurrentRequests()) {
            System.out.println(serviceName + ": WARNING -- pool size " + config.maxPoolSize()
                    + " is SMALLER than expected concurrency " + config.expectedConcurrentRequests() + ", requests will QUEUE");
        } else {
            System.out.println(serviceName + ": pool size " + config.maxPoolSize()
                    + " comfortably covers expected concurrency " + config.expectedConcurrentRequests());
        }
    }

    public static void main(String[] args) {
        validatePoolSizing("order-service", loadOrderServiceConfig());
        validatePoolSizing("audit-service", loadAuditServiceConfig());

        int totalConnectionsAcrossServices = loadOrderServiceConfig().maxPoolSize() + loadAuditServiceConfig().maxPoolSize();
        System.out.println("Combined max connections across BOTH services: " + totalConnectionsAcrossServices
                + " -- even with SEPARATE databases, the database SERVER hosting both still has a total connection ceiling to respect.");
    }
}
```

How to run: `java SizedPoolsPerServiceLoad.java`

`loadOrderServiceConfig` sizes its pool at `30` for an expected `25` concurrent requests — comfortably sufficient. `loadAuditServiceConfig` sizes its pool much smaller, at `5`, matching its own much lower expected concurrency of `2`. `validatePoolSizing` checks each service's own numbers independently, and the final line highlights a subtlety: even though `order-db` and `audit-db` are logically separate databases, if they happen to be hosted on the same physical database server, the *sum* of every service's pool size still matters for that server's total connection capacity — per-service isolation in configuration doesn't automatically mean unlimited resources at the infrastructure layer.

## 6. Walkthrough

Trace `SizedPoolsPerServiceLoad.main` in order. **First**, `validatePoolSizing("order-service", loadOrderServiceConfig())` runs: `loadOrderServiceConfig()` returns a config with `maxPoolSize=30` and `expectedConcurrentRequests=25`. Inside `validatePoolSizing`, `30 < 25` is `false`, so the `else` branch runs, printing that the pool comfortably covers expected concurrency.

**Next**, `validatePoolSizing("audit-service", loadAuditServiceConfig())` runs: `loadAuditServiceConfig()` returns `maxPoolSize=5` and `expectedConcurrentRequests=2`. Again `5 < 2` is `false`, so the same comfortable-coverage branch prints for this service too — its much smaller pool is entirely appropriate for its much smaller expected load.

**Then**, `main` computes `totalConnectionsAcrossServices` by summing both services' `maxPoolSize()` values directly, getting `30 + 5 = 35`.

**Finally**, `main` prints this combined total along with a note about the database server's overall connection ceiling — illustrating that per-service datasource configuration correctly isolates *which database* each service talks to, but doesn't by itself account for *how many total connections* a shared physical database server can sustain across every service hosted on it.

```
order-service:  pool=30, expected=25  -> comfortably sized
audit-service:  pool=5,  expected=2   -> comfortably sized
combined total across BOTH services' pools: 35 -- must still fit the DB SERVER's overall connection limit
```

## 7. Gotchas & takeaways

> Two services having entirely separate `application.yml` datasource configurations does not guarantee their combined connection pools fit within whatever physical database server (or servers) actually hosts those databases — size each pool for that service's own load, but also track the sum across every service sharing infrastructure.

- Each service's `application.yml` should declare `spring.datasource.*` pointing exclusively at that service's own database — never referencing another service's connection details.
- This configuration-level separation is a cheap, mechanical enforcement of [database per service](0304-database-per-service-pattern.md): the coupling simply can't be wired up by accident.
- Size each service's connection pool (`spring.datasource.hikari.maximum-pool-size`) to that service's own expected concurrency, not a copy-pasted default from another service.
- Injecting connection details via environment variables (rather than hardcoding them) lets the same built artifact run correctly against different databases across environments (dev, staging, production).
