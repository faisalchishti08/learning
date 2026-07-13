---
card: microservices
gi: 232
slug: spring-cloud-config-client
title: "Spring Cloud Config Client"
---

## 1. What it is

Spring Cloud Config Client is the counterpart dependency a regular Spring Boot application adds to fetch its configuration from a [Spring Cloud Config Server](0231-spring-cloud-config-server.md) at startup, automatically, before the application's own beans are created — so the fetched values become available through the exact same `@Value`/`@ConfigurationProperties`/`Environment` mechanisms as [ordinary Spring Boot externalized configuration](0228-spring-boot-externalized-configuration-properties-yaml-env-a.md), with no custom HTTP-calling code needed in the consuming application.

## 2. Why & when

Without a dedicated client, a Spring application wanting configuration from a centralized Config Server would need to manually call the server's HTTP API, parse the response, and inject the resulting values into the Spring context early enough that they're available before other beans (which might depend on them) are constructed — timing that's easy to get wrong by hand. Spring Cloud Config Client automates this entirely: adding the dependency and pointing `spring.config.import` (or, in older versions, `spring.cloud.config.uri`) at the Config Server's address is enough for the fetched configuration to be merged into the application's `Environment` before bean creation begins.

Add the Config Client dependency to any Spring Boot service that should pull its configuration from a centralized [Config Server](0231-spring-cloud-config-server.md) rather than relying solely on its own local `application.yaml`. A standalone service with no need for centralized configuration doesn't need this dependency at all.

## 3. Core concept

The Config Client performs its fetch during Spring Boot's configuration-loading phase — before the application context creates its beans — retrieving `{application}/{profile}` from the Config Server and merging the result into the local `Environment` at a precedence position that (by default) outranks the application's own local `application.yaml`, so remote, centrally managed values take priority.

```java
// application.yaml (of the CLIENT application, e.g. order-service)
// spring:
//   application:
//     name: order-service   // used as {application} in the Config Server request
//   config:
//     import: "configserver:http://config-server:8888" // FETCH from here, BEFORE beans are created
// spring.profiles.active: production // used as {profile} in the Config Server request

@RestController
public class OrderController {
    @Value("${db.url}") // resolved from WHATEVER the Config Server returned -- no manual HTTP call anywhere in this class
    String dbUrl;
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="During Spring Boot startup, before any application beans are created, the Config Client fetches configuration from the Config Server and merges it into the local Environment, which application beans then read from normally" >
  <rect x="20" y="20" width="180" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">1. Boot starts</text>

  <rect x="230" y="20" width="180" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">2. Config Client fetches</text>

  <rect x="440" y="20" width="180" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">3. Environment merged</text>

  <rect x="230" y="110" width="180" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="135" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">4. Beans created, read config</text>

  <line x1="200" y1="40" x2="228" y2="40" stroke="#8b949e" marker-end="url(#arr232)"/>
  <line x1="410" y1="40" x2="438" y2="40" stroke="#8b949e" marker-end="url(#arr232)"/>
  <line x1="530" y1="60" x2="320" y2="108" stroke="#8b949e" marker-end="url(#arr232)"/>

  <defs>
    <marker id="arr232" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The fetch happens strictly before bean creation, so every bean sees fully resolved, centrally sourced configuration from the start.

## 5. Runnable example

Scenario: a service startup sequence modeled first with configuration loaded only from a local file (no fetch step at all), then extended to insert a Config Client-style remote fetch that must complete before "beans" are constructed, and finally demonstrating what happens when that fetch fails — the client falling back or failing fast, matching a real Config Client's configurable failure behavior.

### Level 1 — Basic

```java
// File: LocalOnlyStartup.java -- configuration comes ONLY from a local
// source; there is NO remote fetch step in this startup sequence at all.
import java.util.*;

public class LocalOnlyStartup {
    static Map<String, String> localConfig = Map.of("db.url", "jdbc:postgresql://localhost:5432/orders");

    static class OrderBean {
        String dbUrl;
        OrderBean(Map<String, String> config) { this.dbUrl = config.get("db.url"); } // reads LOCAL config only
    }

    public static void main(String[] args) {
        System.out.println("1. Boot starts");
        System.out.println("2. Beans created directly from LOCAL config");
        OrderBean bean = new OrderBean(localConfig);
        System.out.println("3. OrderBean.dbUrl = " + bean.dbUrl);
    }
}
```

**How to run:** `javac LocalOnlyStartup.java && java LocalOnlyStartup` (JDK 17+).

### Level 2 — Intermediate

```java
// File: RemoteFetchBeforeBeans.java -- inserts a REMOTE FETCH step,
// mirroring Config Client, that MUST complete and MERGE into the
// environment BEFORE any bean is constructed.
import java.util.*;

public class RemoteFetchBeforeBeans {
    static Map<String, String> localConfig = new HashMap<>(Map.of("db.url", "jdbc:postgresql://localhost:5432/orders", "retry.count", "3"));

    static Map<String, String> fetchFromConfigServer(String application, String profile) { // mirrors the REAL Config Client HTTP call
        System.out.println("2. Config Client fetching " + application + "/" + profile + " from Config Server...");
        return Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders"); // the SERVER'S authoritative value
    }

    static class OrderBean {
        String dbUrl; int retryCount;
        OrderBean(Map<String, String> environment) {
            this.dbUrl = environment.get("db.url");
            this.retryCount = Integer.parseInt(environment.get("retry.count"));
        }
    }

    public static void main(String[] args) {
        System.out.println("1. Boot starts");

        Map<String, String> remoteConfig = fetchFromConfigServer("order-service", "production"); // STEP 2 -- BEFORE beans
        Map<String, String> mergedEnvironment = new HashMap<>(localConfig);
        mergedEnvironment.putAll(remoteConfig); // remote OVERRIDES local, by DEFAULT Config Client precedence
        System.out.println("3. Environment merged: " + mergedEnvironment);

        OrderBean bean = new OrderBean(mergedEnvironment); // STEP 4 -- created AFTER the merge
        System.out.println("4. OrderBean.dbUrl = " + bean.dbUrl + ", retryCount = " + bean.retryCount);
    }
}
```

**How to run:** `javac RemoteFetchBeforeBeans.java && java RemoteFetchBeforeBeans` (JDK 17+).

Expected output:
```
1. Boot starts
2. Config Client fetching order-service/production from Config Server...
3. Environment merged: {db.url=jdbc:postgresql://prod-db:5432/orders, retry.count=3}
4. OrderBean.dbUrl = jdbc:postgresql://prod-db:5432/orders, retryCount = 3
```

### Level 3 — Advanced

```java
// File: FailFastVsFailoverOnFetchFailure.java -- models Config Client's
// configurable failure behavior: fail-fast (abort startup) vs. tolerant
// (proceed with LOCAL config only) when the Config Server is unreachable.
import java.util.*;

public class FailFastVsFailoverOnFetchFailure {
    static Map<String, String> localConfig = new HashMap<>(Map.of("db.url", "jdbc:postgresql://localhost:5432/orders"));

    static Optional<Map<String, String>> fetchFromConfigServer(boolean simulateServerDown) {
        if (simulateServerDown) return Optional.empty(); // simulates a connection failure
        return Optional.of(Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders"));
    }

    static Map<String, String> resolveEnvironment(boolean failFast, boolean simulateServerDown) {
        Optional<Map<String, String>> remoteConfig = fetchFromConfigServer(simulateServerDown);
        if (remoteConfig.isEmpty()) {
            if (failFast) {
                // mirrors spring.cloud.config.fail-fast=true -- abort startup entirely
                throw new IllegalStateException("Config Server unreachable and fail-fast is enabled -- aborting startup");
            } else {
                System.out.println("  [WARN] Config Server unreachable -- proceeding with LOCAL config only (fail-fast disabled)");
                return localConfig; // TOLERANT -- degrade to local config rather than crash
            }
        }
        Map<String, String> merged = new HashMap<>(localConfig);
        merged.putAll(remoteConfig.get());
        return merged;
    }

    public static void main(String[] args) {
        System.out.println("=== Config Server reachable ===");
        System.out.println(resolveEnvironment(true, false));

        System.out.println("\n=== Config Server DOWN, fail-fast=false (tolerant) ===");
        System.out.println(resolveEnvironment(false, true));

        System.out.println("\n=== Config Server DOWN, fail-fast=true ===");
        try {
            resolveEnvironment(true, true);
        } catch (IllegalStateException e) {
            System.out.println("Caught expected startup abort: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac FailFastVsFailoverOnFetchFailure.java && java FailFastVsFailoverOnFetchFailure` (JDK 17+).

Expected output:
```
=== Config Server reachable ===
{db.url=jdbc:postgresql://prod-db:5432/orders}

=== Config Server DOWN, fail-fast=false (tolerant) ===
  [WARN] Config Server unreachable -- proceeding with LOCAL config only (fail-fast disabled)
{db.url=jdbc:postgresql://localhost:5432/orders}

=== Config Server DOWN, fail-fast=true ===
Caught expected startup abort: Config Server unreachable and fail-fast is enabled -- aborting startup
```

## 6. Walkthrough

1. **Level 1, no remote step exists** — `OrderBean` is constructed directly from `localConfig`; there is no notion of fetching anything remotely, and this program's structure has no place where a Config Client-style step would even fit.
2. **Level 2, inserting the fetch as its own step** — `fetchFromConfigServer` is called and completes (`remoteConfig` is fully populated) *before* `mergedEnvironment` is built and, critically, before `OrderBean` is constructed — this ordering (fetch, then merge, then create beans) is exactly the sequencing Spring Cloud Config Client enforces automatically during real application startup.
3. **Level 2, remote precedence over local** — `mergedEnvironment.putAll(remoteConfig)` copies the remote map's entries over the local ones, so `db.url` ends up as the Config Server's value (`prod-db`) rather than the local file's (`localhost`), matching Config Client's default precedence of remote-over-local for overlapping keys, while `retry.count` (present only locally) survives unchanged.
4. **Level 3, modeling a fetch that can fail** — `fetchFromConfigServer` now returns an `Optional`, empty when `simulateServerDown` is true, standing in for a real network failure connecting to an unreachable Config Server.
5. **Level 3, the fail-fast path** — when `remoteConfig` is empty and `failFast` is true, `resolveEnvironment` throws immediately, mirroring `spring.cloud.config.fail-fast=true`: a real application configured this way refuses to start at all if it cannot reach its Config Server, on the reasoning that starting with incomplete or stale configuration could be worse than not starting.
6. **Level 3, the tolerant fallback path** — when `remoteConfig` is empty and `failFast` is false, `resolveEnvironment` logs a warning and returns `localConfig` unchanged instead of throwing, mirroring a Config Client configured to tolerate a Config Server outage by degrading to whatever local configuration is available — the three `main` calls demonstrate all three outcomes side by side: a successful fetch, a tolerant degradation, and a fail-fast abort, corresponding to the three real configurations a Config Client deployment can be set up with.

## 7. Gotchas & takeaways

> **Gotcha:** whether an application should fail fast or degrade gracefully when its Config Server is unreachable is a real availability trade-off, not a default to leave unexamined — fail-fast prevents starting with potentially wrong or stale configuration but makes the Config Server a hard dependency for every consuming service's startup (a Config Server outage can then prevent restarts or scale-out across the whole fleet); choose deliberately per service based on how safe it actually is to start with local-only configuration.

- Spring Cloud Config Client fetches configuration from a [Config Server](0231-spring-cloud-config-server.md) automatically during Spring Boot's startup sequence, before application beans are created, requiring no custom HTTP-calling code.
- Fetched, remote configuration takes precedence over the application's own local `application.yaml` for overlapping keys, by default.
- The client's behavior on a failed fetch is configurable — fail-fast aborts startup entirely, while a tolerant configuration degrades to whatever local configuration is available.
- This is a real availability trade-off: fail-fast guards against starting with wrong configuration but makes the Config Server a hard dependency for every consumer's startup and restart.
- Once fetched, remote values are exposed through the exact same `@Value`/`@ConfigurationProperties`/`Environment` mechanisms as ordinary local Spring Boot configuration — application code never distinguishes between local and remote sources.
