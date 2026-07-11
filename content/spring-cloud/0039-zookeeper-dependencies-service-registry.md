---
card: spring-cloud
gi: 39
slug: zookeeper-dependencies-service-registry
title: "Zookeeper dependencies & service registry"
---

## 1. What it is

Beyond service discovery, Spring Cloud Zookeeper's `DependencyServiceInstanceListSupplier` and related dependency configuration let a service declare, in configuration, exactly which other services it depends on and how to reach them — including static aliasing to non-ZooKeeper-managed services — layered on top of ZooKeeper's `ServiceRegistry` (the same `ServiceRegistry`/`Registration` abstraction from Spring Cloud Commons, covered in the Overview section).

```properties
spring.cloud.zookeeper.dependencies.billing.path=/services/billing-service
spring.cloud.zookeeper.dependencies.billing.load-balancer-type=ROUND_ROBIN
spring.cloud.zookeeper.dependencies.billing.content-type-template=application/vnd.billing.v1+json
```

```java
// resolved via the alias "billing", not the raw ZooKeeper path
restTemplate.getForObject("http://billing/invoices/42", Invoice.class);
```

## 2. Why & when

Plain ZooKeeper discovery (the previous card) resolves a service by its literal registered name. Dependency configuration adds a layer on top: naming an *alias* for each dependency the current service actually calls, decoupling the code's logical name for a collaborator from the exact path or versioned API contract it maps to underneath — useful when a dependency's real registration path or API version needs to change without touching every caller's code.

Reach for explicit Zookeeper dependency configuration when:

- Multiple services depend on a shared collaborator and you want a single place (configuration, not code) that names and documents those dependencies — effectively self-documenting the service's dependency graph.
- Different dependencies need different load-balancing strategies (`ROUND_ROBIN` vs `STICKY`, for instance) and you want that expressed per-dependency in configuration rather than hardcoded in each call site.
- A dependency's registered path or API version might change, and callers should be insulated from that by referring to it through a stable alias.

## 3. Core concept

```
 application code:  restTemplate.getForObject("http://billing/...")
                            |
        alias "billing" resolves via configuration to:
                            |
        ZooKeeper path:  /services/billing-service
                            |
        load-balancer-type:  ROUND_ROBIN across all live znodes under that path
```

The alias is the stable contract application code depends on; everything underneath it — the real path, the load-balancing strategy, the content type — is configuration, not code.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code calls a stable alias which configuration maps to a real ZooKeeper registry path, insulating callers from changes to the underlying registration">
  <rect x="30" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">code calls</text>
  <text x="120" y="108" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">http://billing/...</text>

  <rect x="250" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">dependency config</text>
  <text x="340" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">alias -&gt; path + strategy</text>

  <rect x="470" y="70" width="150" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">/services/</text>
  <text x="545" y="108" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">billing-service</text>

  <line x1="210" y1="95" x2="248" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a39)"/>
  <line x1="430" y1="95" x2="468" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a39)"/>

  <defs><marker id="a39" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

An alias sits between calling code and the real registry path, so the underlying path or strategy can change without touching call sites.

## 5. Runnable example

The scenario: `orders-service` calling `billing-service` by a stable alias. Start with a direct hardcoded path reference, then add alias-based indirection, then add a live migration of the underlying path — proving the caller's code never had to change.

### Level 1 — Basic

Direct reference to the raw registry path — the coupling this feature removes.

```java
import java.util.*;

public class ZkDependenciesLevel1 {
    static Map<String, List<String>> registry = Map.of(
            "/services/billing-service", List.of("10.0.2.1:8080", "10.0.2.2:8080")
    );

    static String callBilling(String invoiceId) {
        List<String> instances = registry.get("/services/billing-service"); // hardcoded path in call site
        String target = instances.get(0);
        return "GET http://" + target + "/invoices/" + invoiceId;
    }

    public static void main(String[] args) {
        System.out.println(callBilling("42"));
    }
}
```

How to run: `java ZkDependenciesLevel1.java`

The exact ZooKeeper path `/services/billing-service` is baked directly into `callBilling` — if that path or its structure ever changes (a rename, a versioned re-registration under a new path), every call site referencing it must be found and updated.

### Level 2 — Intermediate

Add a dependency configuration layer: an alias maps to the real path, and call sites reference only the alias.

```java
import java.util.*;

public class ZkDependenciesLevel2 {
    record DependencyConfig(String path, String loadBalancerType) {}

    static Map<String, DependencyConfig> dependencies = Map.of(
            "billing", new DependencyConfig("/services/billing-service", "ROUND_ROBIN")
    );

    static Map<String, List<String>> registry = Map.of(
            "/services/billing-service", List.of("10.0.2.1:8080", "10.0.2.2:8080")
    );

    static String call(String alias, String path) {
        DependencyConfig config = dependencies.get(alias); // code only knows the alias
        List<String> instances = registry.get(config.path());
        String target = instances.get(0); // simplified: real round-robin covered in an earlier card
        return "GET http://" + target + path;
    }

    public static void main(String[] args) {
        System.out.println(call("billing", "/invoices/42")); // call site never mentions the real path
    }
}
```

How to run: `java ZkDependenciesLevel2.java`

`call` now takes an `alias` ("billing"), looks up its `DependencyConfig` (which holds the real ZooKeeper path and the configured load-balancer strategy), and resolves instances through that indirection. The call site — `call("billing", "/invoices/42")` — never references `/services/billing-service` directly; it's exactly analogous to calling `http://billing/invoices/42` through a `RestTemplate` configured with Zookeeper dependency support.

### Level 3 — Advanced

Simulate a real migration: `billing-service` moves to a new registration path (say, a v2 rollout under a new path while the old one drains), and show that only the dependency configuration needs updating — no call sites change.

```java
import java.util.*;

public class ZkDependenciesLevel3 {
    record DependencyConfig(String path, String loadBalancerType) {}

    static Map<String, DependencyConfig> dependencies = new HashMap<>(Map.of(
            "billing", new DependencyConfig("/services/billing-service", "ROUND_ROBIN")
    ));

    static Map<String, List<String>> registry = new HashMap<>(Map.of(
            "/services/billing-service", List.of("10.0.2.1:8080", "10.0.2.2:8080"),
            "/services/billing-service-v2", List.of("10.0.3.1:8080", "10.0.3.2:8080")
    ));

    static int callCounter = 0;

    static String call(String alias, String path) {
        DependencyConfig config = dependencies.get(alias);
        List<String> instances = registry.get(config.path());
        String target = instances.get(callCounter++ % instances.size()); // round-robin across current instances
        return "GET http://" + target + path;
    }

    public static void main(String[] args) {
        System.out.println("before migration: " + call("billing", "/invoices/1"));
        System.out.println("before migration: " + call("billing", "/invoices/2"));

        // operators migrate billing-service to v2 -- ONLY the dependency config changes, not call sites
        dependencies.put("billing", new DependencyConfig("/services/billing-service-v2", "ROUND_ROBIN"));

        System.out.println("after migration:  " + call("billing", "/invoices/3"));
        System.out.println("after migration:  " + call("billing", "/invoices/4"));
    }
}
```

How to run: `java ZkDependenciesLevel3.java`

Before the migration, `call("billing", ...)` resolves through `/services/billing-service` and hits `10.0.2.x` addresses. After `dependencies.put("billing", ...)` swaps the alias's target path to `/services/billing-service-v2`, the exact same call site — `call("billing", "/invoices/3")` — now resolves through the new path and hits `10.0.3.x` addresses instead, with zero changes to any calling code. Only the configuration changed.

## 6. Walkthrough

Trace Level 3's four `println` calls in order.

1. `call("billing", "/invoices/1")` runs first — it looks up `dependencies.get("billing")`, currently pointing at `/services/billing-service`, resolves `registry.get(...)` to the two `10.0.2.x` addresses, and picks index `0 % 2 = 0` (`callCounter` was `0`), producing `GET http://10.0.2.1:8080/invoices/1`.
2. `call("billing", "/invoices/2")` runs next — same alias resolution, but `callCounter` is now `1`, so index `1 % 2 = 1` picks the second instance: `GET http://10.0.2.2:8080/invoices/2`. This is the round-robin behavior spreading load across the currently-configured path's instances.
3. `dependencies.put("billing", ...)` runs — this models an operator (or a config-driven rollout process) updating the ZooKeeper dependency configuration to point the `billing` alias at a new path, `/services/billing-service-v2`, perhaps as part of a versioned API migration where v2 instances register under a new path while v1 instances drain and are decommissioned.
4. `call("billing", "/invoices/3")` runs — the alias lookup now returns the *new* `DependencyConfig`, so `registry.get(...)` resolves against `/services/billing-service-v2` instead, picking `10.0.3.1:8080` (`callCounter` is `2`, `2 % 2 = 0`).
5. `call("billing", "/invoices/4")` runs — `callCounter` is `3`, `3 % 2 = 1`, picking `10.0.3.2:8080`. Both post-migration calls hit the new instance set, and critically, the call-site code (`call("billing", ...)`) is textually identical before and after the migration — every change happened in configuration.

```
before: alias "billing" -> /services/billing-service    -> 10.0.2.1, 10.0.2.2
                                    |
                    dependencies.put("billing", new path)
                                    |
after:  alias "billing" -> /services/billing-service-v2 -> 10.0.3.1, 10.0.3.2

call sites: unchanged in both cases
```

## 7. Gotchas & takeaways

> **Gotcha:** dependency aliases only help if every caller consistently goes through them — if some code paths call the raw ZooKeeper path directly (bypassing the alias, as in Level 1) while others use the alias, a migration like Level 3's will silently miss the direct callers, leaving them pointed at a decommissioned path.

- Dependency configuration decouples the *logical name* a service's code depends on from the *physical path* that name currently resolves to — the same principle service discovery applies to individual instances, applied one level up to whole dependencies.
- Per-dependency load-balancer strategy configuration means different collaborators can be balanced differently without touching call-site code — a natural fit for services with different traffic patterns or session-affinity needs.
- This pattern is Zookeeper-specific tooling, but the underlying idea — resolve dependencies by stable alias, not hardcoded path — is the same motivation behind calling services by logical name through `DiscoveryClient` in Eureka or Consul.
- A path migration is safe specifically because it's a configuration change, not a code change — it can be rolled out and rolled back independently of any application deployment.
