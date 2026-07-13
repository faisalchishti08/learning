---
card: microservices
gi: 219
slug: centralized-configuration-server
title: "Centralized configuration server"
---

## 1. What it is

A centralized configuration server is a dedicated service that stores and serves configuration for every other service in a system, replacing per-service, per-instance config files with one authoritative source that all services fetch their settings from at startup (and optionally refresh from at runtime).

## 2. Why & when

[Externalized configuration](0218-externalized-configuration-12-factor.md) solves the "same artifact, different environments" problem, but doesn't by itself solve a different one: in a system with dozens of services, each with its own config files scattered across dozens of repositories or deployment scripts, a shared setting (a common timeout, a shared endpoint) that needs to change means hunting down and updating every copy individually — error-prone, and easy to miss one. A centralized configuration server addresses this by giving every service a single place to fetch configuration from, so a shared value lives in exactly one location and every service consuming it sees the same, current value.

Introduce a centralized configuration server once a system has enough services (and enough configuration duplicated or drifting across them) that managing config file-by-file becomes a real maintenance burden — a handful of independent services with their own, non-overlapping config rarely needs one. [Spring Cloud Config Server](0231-spring-cloud-config-server.md), covered later in this section, is Spring's implementation of this pattern.

## 3. Core concept

A centralized configuration server exposes configuration over an API (commonly HTTP), keyed by service name and environment/profile, and each service fetches its configuration from that server at startup rather than reading it from a local file bundled with its own deployment.

```java
// a service FETCHING its configuration from a centralized config server, rather than reading a local file
interface ConfigServerClient { Map<String, String> fetchConfig(String serviceName, String profile); }

class HttpConfigServerClient implements ConfigServerClient {
    public Map<String, String> fetchConfig(String serviceName, String profile) {
        // GET http://config-server/order-service/production -- ONE authoritative source
        return Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders", "timeout.ms", "3000");
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three services -- order, inventory, payment -- each fetch their configuration from one centralized configuration server, rather than each maintaining its own scattered config files" >
  <rect x="245" y="20" width="150" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Config server</text>

  <rect x="30" y="130" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="154" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order-service</text>

  <rect x="255" y="130" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="154" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">inventory-service</text>

  <rect x="480" y="130" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="154" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">payment-service</text>

  <line x1="95" y1="128" x2="290" y2="67" stroke="#8b949e" marker-end="url(#arr219)"/>
  <line x1="320" y1="128" x2="320" y2="67" stroke="#8b949e" marker-end="url(#arr219)"/>
  <line x1="545" y1="128" x2="350" y2="67" stroke="#8b949e" marker-end="url(#arr219)"/>

  <defs>
    <marker id="arr219" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Every service fetches from one authoritative source instead of each keeping its own scattered copy.

## 5. Runnable example

Scenario: three services each start with their own duplicated, locally hard-coded shared setting (showing how a shared-value change means editing every copy), refactor to fetch that same setting from one simulated centralized config server, and finally demonstrate updating the value in ONE place instantly affecting all three services' next fetch.

### Level 1 — Basic

```java
// File: DuplicatedLocalConfig.java -- THREE "services" each with their OWN
// copy of a shared setting, hard-coded independently.
public class DuplicatedLocalConfig {
    static String orderServiceTimeout = "3000"; // DUPLICATE #1
    static String inventoryServiceTimeout = "3000"; // DUPLICATE #2
    static String paymentServiceTimeout = "3000"; // DUPLICATE #3

    public static void main(String[] args) {
        System.out.println("order-service timeout: " + orderServiceTimeout);
        System.out.println("inventory-service timeout: " + inventoryServiceTimeout);
        System.out.println("payment-service timeout: " + paymentServiceTimeout);
        System.out.println("Changing the shared timeout means editing THREE separate constants -- easy to miss one.");
    }
}
```

**How to run:** `javac DuplicatedLocalConfig.java && java DuplicatedLocalConfig` (JDK 17+).

### Level 2 — Intermediate

```java
// File: FetchFromCentralConfigServer.java -- all THREE services now fetch
// the SAME shared setting from ONE centralized config server simulation.
import java.util.*;

public class FetchFromCentralConfigServer {
    static class ConfigServer { // the ONE authoritative source
        Map<String, String> sharedSettings = new HashMap<>(Map.of("timeout.ms", "3000"));
        String get(String key) { return sharedSettings.get(key); }
    }

    static ConfigServer configServer = new ConfigServer();

    static String fetchTimeoutFor(String serviceName) {
        return configServer.get("timeout.ms"); // EVERY service fetches from the SAME source
    }

    public static void main(String[] args) {
        System.out.println("order-service timeout: " + fetchTimeoutFor("order-service"));
        System.out.println("inventory-service timeout: " + fetchTimeoutFor("inventory-service"));
        System.out.println("payment-service timeout: " + fetchTimeoutFor("payment-service"));
        System.out.println("All three fetched from ONE ConfigServer instance -- one source of truth.");
    }
}
```

**How to run:** `javac FetchFromCentralConfigServer.java && java FetchFromCentralConfigServer` (JDK 17+).

Expected output:
```
order-service timeout: 3000
inventory-service timeout: 3000
payment-service timeout: 3000
All three fetched from ONE ConfigServer instance -- one source of truth.
```

### Level 3 — Advanced

```java
// File: OneChangePropagatesToAll.java -- updating the shared setting in
// the config server ONCE is reflected by EVERY service's next fetch,
// with NO changes needed to any individual service's code.
import java.util.*;

public class OneChangePropagatesToAll {
    static class ConfigServer {
        Map<String, String> sharedSettings = new HashMap<>(Map.of("timeout.ms", "3000"));
        String get(String key) { return sharedSettings.get(key); }
        void update(String key, String value) { sharedSettings.put(key, value); } // ONE update point
    }

    static ConfigServer configServer = new ConfigServer();
    static String fetchTimeoutFor(String serviceName) { return configServer.get("timeout.ms"); }

    public static void main(String[] args) {
        System.out.println("=== before the change ===");
        for (String svc : List.of("order-service", "inventory-service", "payment-service")) {
            System.out.println(svc + " timeout: " + fetchTimeoutFor(svc));
        }

        configServer.update("timeout.ms", "5000"); // ONE change, at the source

        System.out.println("\n=== after updating ONLY the config server ===");
        for (String svc : List.of("order-service", "inventory-service", "payment-service")) {
            System.out.println(svc + " timeout: " + fetchTimeoutFor(svc)); // ALL three reflect the new value
        }
        System.out.println("\nNo service's own code changed -- ONE update at the source reached all three.");
    }
}
```

**How to run:** `javac OneChangePropagatesToAll.java && java OneChangePropagatesToAll` (JDK 17+).

Expected output:
```
=== before the change ===
order-service timeout: 3000
inventory-service timeout: 3000
payment-service timeout: 3000

=== after updating ONLY the config server ===
order-service timeout: 5000
inventory-service timeout: 5000
payment-service timeout: 5000

No service's own code changed -- ONE update at the source reached all three.
```

## 6. Walkthrough

1. **Level 1, the duplication problem** — `orderServiceTimeout`, `inventoryServiceTimeout`, and `paymentServiceTimeout` are three independent constants holding the identical value `"3000"`; nothing in the code enforces that they stay in sync, and a real-world equivalent (three separate config files) risks drifting apart over time as changes are applied inconsistently.
2. **Level 2, introducing the single source** — `ConfigServer` holds `sharedSettings` in one place, and `fetchTimeoutFor` — called identically for all three simulated services — reads from that single `configServer` instance rather than from any per-service constant; there is now exactly one place the value `"3000"` lives.
3. **Level 2, why this matters even before anything changes** — even though the printed output is identical to Level 1's, the *structure* has changed: three call sites now depend on one shared object, meaning a future update only needs to touch that one object.
4. **Level 3, the single update point** — `ConfigServer.update` is the only method that mutates `sharedSettings`, and `main` calls it exactly once, changing `"timeout.ms"` from `"3000"` to `"5000"`.
5. **Level 3, propagation without redeployment** — the second loop over the three service names calls `fetchTimeoutFor` again, and because that method always reads live from `configServer.sharedSettings` (not a cached copy taken earlier), all three services immediately reflect the updated `"5000"` value — no service's own code, constant, or deployment artifact needed to change.
6. **Level 3, the takeaway made concrete** — comparing the "before" and "after" blocks side by side shows the exact benefit centralization provides: a configuration change made in one place (the config server) is observed everywhere it's consumed, in contrast to Level 1's structure where the same change would have required editing three separate locations.

## 7. Gotchas & takeaways

> **Gotcha:** centralizing configuration also centralizes a single point of failure and a single point of blast-radius for a bad change — if the config server is unreachable at a service's startup, or if an update pushes a broken value, every dependent service is affected simultaneously; production centralized-config setups typically pair this pattern with local caching/fallback (so a temporarily unreachable config server doesn't take down every service) and staged rollout of configuration changes.

- A centralized configuration server gives every service one authoritative source for shared settings, instead of each service maintaining its own, potentially drifting copy.
- It builds on top of [externalized configuration](0218-externalized-configuration-12-factor.md) — externalizing moves config out of the artifact; centralizing consolidates where that externalized config actually lives.
- Introduce one once config duplication across many services becomes a real maintenance burden, not for a small number of services with independent, non-overlapping settings.
- A single update at the source can propagate to every consuming service without any of those services being redeployed or their own code changed.
- Centralizing configuration also centralizes risk — a config server outage or a bad pushed value affects every dependent service at once, which is why production setups typically add local caching/fallback alongside centralization.
