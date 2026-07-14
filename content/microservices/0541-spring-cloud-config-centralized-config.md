---
card: microservices
gi: 541
slug: spring-cloud-config-centralized-config
title: "Spring Cloud Config (centralized config)"
---

## 1. What it is

**Spring Cloud Config** provides a Config Server (a dedicated Spring Boot application serving configuration over HTTP, typically backed by a Git repository) and a Config Client (the library any Spring Boot service uses to fetch its configuration from that server at startup, rather than reading purely local `application.yml` files). Instead of every service in a fleet carrying its own scattered configuration files, potentially drifting or duplicating shared values, all services fetch their configuration from one centralized source of truth, versioned in Git alongside a full change history.

## 2. Why & when

You reach for centralized configuration once a system grows past a handful of services, because scattered per-service configuration files create real coordination and consistency problems:

- **Shared configuration values (a common downstream URL, a shared feature flag, common resilience timeouts) duplicated across many services' local config files inevitably drift** — one service's copy gets updated during a change, another's is forgotten, and now the fleet is running inconsistent values with no single place to check what's actually correct.
- **A Git-backed Config Server gives configuration the same versioning, review, and audit trail as code** — every configuration change is a commit, reviewable via pull request, revertible via `git revert`, and attributable to whoever made it, rather than a config file edited directly on a server with no history.
- **Combined with [`@RefreshScope` and Spring Cloud Bus](0540-spring-cloud-context-bootstrap-context.md), centralized configuration enables fleet-wide, zero-downtime configuration changes** — update the value once in the Config Server-backed Git repo, trigger a refresh, and every consuming instance picks up the change without a redeploy.
- **You reach for it once you have more than a trivial number of services**, or as soon as any configuration value genuinely needs to be shared and kept consistent across services — for a single monolithic application with entirely local configuration, the operational overhead of running a Config Server may not be justified.

## 3. Core concept

Think of a large organization's HR policy handbook. If every department printed and maintained its own physical copy, updates would require re-printing and redistributing to every department individually, and inevitably some departments would be working from an outdated printed copy nobody remembered to update. A single, centrally maintained handbook — versioned, with a clear history of every revision — that every department consults directly, rather than keeping their own separate copies, guarantees everyone is always looking at the same, current version, and every past revision is fully auditable.

Concretely:

1. **The Config Server is a standalone Spring Boot application** (`@EnableConfigServer`) pointed at a backing Git repository (or, alternatively, a filesystem, Vault, or JDBC source), exposing configuration files over a REST API keyed by application name and active profile.
2. **Each Config Client service specifies its own application name** (`spring.application.name=order-service`) and points at the Config Server's URL (`spring.config.import=configserver:http://config-server:8888`); at startup, it fetches `order-service.yml` (and any shared `application.yml` common to all services) from the server.
3. **Profile-specific configuration files** (`order-service-production.yml`, `order-service-staging.yml`) let the same Config Server serve different values per environment, resolved automatically based on which profile the requesting client is running with.
4. **Because the backing store is Git, every configuration change is a normal commit** — reviewable, revertible, and attributable — and the Config Server simply serves whatever the currently-checked-out branch/commit contains, making "what configuration is currently live" as inspectable as "what code is currently deployed."

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple services fetch their configuration from one centralized Config Server backed by a Git repository, instead of maintaining scattered local config files that can drift">
  <rect x="270" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="360" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Config Server (Git-backed)</text>

  <rect x="20" y="110" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-service</text>
  <rect x="250" y="110" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">inventory-service</text>
  <rect x="480" y="110" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">pricing-service</text>

  <line x1="95" y1="110" x2="300" y2="60" stroke="#8b949e" marker-end="url(#a6)"/>
  <line x1="325" y1="110" x2="345" y2="60" stroke="#8b949e" marker-end="url(#a6)"/>
  <line x1="555" y1="110" x2="400" y2="60" stroke="#8b949e" marker-end="url(#a6)"/>
  <text x="330" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ONE source of truth, versioned in Git, instead of scattered per-service files</text>
  <defs><marker id="a6" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Every service fetches from one Git-backed Config Server rather than maintaining its own potentially-drifting local configuration.

## 5. Runnable example

Scenario: multiple services needing consistent shared configuration. We start with a plain Java model of the drift problem with scattered config, extend it to a centralized fetch model, then show the real Config Server/Config Client setup.

### Level 1 — Basic

```java
// File: ScatteredConfigDrift.java -- models the DRIFT problem: each
// "service" keeps its OWN copy of a shared value, and they've drifted apart.
import java.util.*;

public class ScatteredConfigDrift {
    static Map<String, String> orderServiceOwnConfig = Map.of("downstream.pricing.timeout-ms", "500");
    static Map<String, String> inventoryServiceOwnConfig = Map.of("downstream.pricing.timeout-ms", "2000"); // DRIFTED! forgotten update

    public static void main(String[] args) {
        System.out.println("order-service's pricing timeout: " + orderServiceOwnConfig.get("downstream.pricing.timeout-ms") + "ms");
        System.out.println("inventory-service's pricing timeout: " + inventoryServiceOwnConfig.get("downstream.pricing.timeout-ms") + "ms");
        System.out.println("Problem: these were meant to be the SAME shared value, but drifted -- nobody remembered to update both copies.");
    }
}
```

How to run: `java ScatteredConfigDrift.java`

Two services' own local configuration copies of what was supposed to be the same shared timeout value have silently diverged — one was updated during a past change, the other wasn't, and nothing catches this inconsistency until it causes confusing, inconsistent behavior in production.

### Level 2 — Intermediate

```java
// File: CentralizedFetchModel.java -- models fetching from ONE
// centralized source instead of maintaining separate local copies.
import java.util.*;

public class CentralizedFetchModel {
    // ONE shared source of truth, modeling a Git-backed Config Server
    static Map<String, String> centralConfig = new HashMap<>(Map.of("downstream.pricing.timeout-ms", "500"));

    static String fetchConfig(String serviceName, String key) {
        System.out.println("[" + serviceName + "] fetching '" + key + "' from centralized Config Server...");
        return centralConfig.get(key); // BOTH services fetch from the SAME source
    }

    public static void main(String[] args) {
        System.out.println("order-service's pricing timeout: " + fetchConfig("order-service", "downstream.pricing.timeout-ms") + "ms");
        System.out.println("inventory-service's pricing timeout: " + fetchConfig("inventory-service", "downstream.pricing.timeout-ms") + "ms");
        System.out.println("Both services now see the IDENTICAL value -- drift is structurally impossible, since there's only one copy.");
    }
}
```

How to run: `java CentralizedFetchModel.java`

Both services call `fetchConfig`, reading from the same `centralConfig` map — there's no way for their values to diverge, since there's only one copy to read from at all, exactly the guarantee a Git-backed Config Server provides for real services across a fleet.

### Level 3 — Advanced

```java
// File: ConfigServerClientRealShape.java -- the REAL Config Server and
// Config Client setup, shown as illustrative configuration and a client
// bean that consumes the fetched, centrally-sourced value.
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.config.server.EnableConfigServer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

public class ConfigServerClientRealShape {

    // --- the Config Server itself: a standalone Spring Boot application ---
    @SpringBootApplication
    @EnableConfigServer
    static class ConfigServerApplication {
        public static void main(String[] args) { SpringApplication.run(ConfigServerApplication.class, args); }
        // application.yml for this server would include:
        //   spring.cloud.config.server.git.uri: https://github.com/example/config-repo
    }

    // --- a Config CLIENT service, e.g. order-service ---
    @Component
    static class PricingClientConfig {
        // this value is fetched from the Config Server's centrally-stored
        // order-service.yml (or shared application.yml), NOT a local file
        @Value("${downstream.pricing.timeout-ms}")
        private int pricingTimeoutMs;

        int getPricingTimeoutMs() { return pricingTimeoutMs; }
    }

    // order-service's own application.yml would include:
    //   spring.application.name: order-service
    //   spring.config.import: configserver:http://config-server:8888
}
```

How to run: requires running a separate Config Server application (`spring-cloud-config-server` dependency, `@EnableConfigServer`, pointed at a real Git repository containing `order-service.yml`/`inventory-service.yml`/`application.yml`), plus each client service depending on `spring-cloud-starter-config` and setting `spring.config.import=configserver:http://config-server:8888`; run both the Config Server and a client service via `mvn spring-boot:run` to see the client's `@Value`-bound field populated from the centrally-stored Git file.

`PricingClientConfig`'s `@Value("${downstream.pricing.timeout-ms}")` is populated from whatever the Config Server currently serves for `order-service` — if `inventory-service` also reads the same property key from a shared `application.yml` in the same Git repository, both services are guaranteed to read the identical value, since there's exactly one file being consulted by both.

## 6. Walkthrough

Trace what happens when `order-service` starts up, configured with `spring.config.import=configserver:http://config-server:8888`, end to end:

1. **Spring Boot's configuration-loading machinery recognizes the `configserver:` import** early in its startup sequence, before most application beans are created.
2. **It issues an HTTP request to the Config Server**: conceptually, `GET http://config-server:8888/order-service/default` (application name `order-service`, profile `default`) — the Config Server's own REST API convention.
3. **The Config Server, upon receiving this request, checks out (or already has checked out) the configured Git repository**, locates `order-service.yml` (and the shared `application.yml`, if present, as a lower-priority fallback), and returns their merged contents as a JSON response describing property sources.
4. **`order-service`'s Spring Boot application merges this fetched configuration into its own `Environment`**, alongside any local `application.yml` values (with the Config Server's values typically taking precedence, depending on configured property source ordering).
5. **`PricingClientConfig`'s `@Value("${downstream.pricing.timeout-ms}")` field is bound during bean creation**, reading `500` (or whatever the Git-backed `order-service.yml` or shared `application.yml` currently specifies) from the now-merged `Environment`.
6. **If `inventory-service` starts up against the same Config Server and the same shared `application.yml`**, its own equivalent `@Value`-bound field reads the identical `500` — both services are guaranteed consistent, because they both ultimately read from the same underlying Git file, not from separately-maintained local copies that could have drifted apart.

## 7. Gotchas & takeaways

> **Gotcha:** the Config Server becomes a hard startup dependency for every client service using `spring.config.import=configserver:...` without the `optional:` prefix — if the Config Server is unreachable when a client starts, that client fails to start at all; using `optional:configserver:...` lets the client fall back to local configuration instead, at the cost of silently missing centrally-managed values if the server happens to be down.

- Centralized, Git-backed configuration eliminates drift between services that are meant to share the same configuration value, since there's only one file to read from rather than separately-maintained local copies.
- Every configuration change becomes a normal Git commit — reviewable, revertible, and attributable — giving configuration the same change-management discipline as code.
- Combine with `@RefreshScope` and Spring Cloud Bus for fleet-wide, zero-downtime configuration updates: change the value once in Git, trigger a refresh, and every consuming instance picks it up without a redeploy.
- Weigh the operational cost of running and maintaining a Config Server against the actual benefit for your fleet's size — a small number of services with little truly shared configuration may not need this centralization yet.
