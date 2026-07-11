---
card: spring-cloud
gi: 37
slug: consul-kv-config
title: "Consul KV config"
---

## 1. What it is

Consul's key-value store doubles as a Spring Cloud Config backend: instead of Git or a database (covered under Spring Cloud Config earlier), configuration properties live as keys under a path in Consul's KV store, and `spring.config.import=consul:` pulls them into the application's `Environment` at startup, the same way `spring.config.import=configserver:` does for Config Server.

```properties
spring.application.name=orders-service
spring.config.import=consul:localhost:8500
spring.cloud.consul.config.prefix=config
spring.cloud.consul.config.format=yaml
```

```
Consul KV layout:
  config/orders-service/data       (YAML/properties blob for this app)
  config/orders-service,prod/data  (profile-specific overrides for the "prod" profile)
  config/application/data          (shared defaults across all applications)
```

## 2. Why & when

If Consul is already the service registry (from the previous two cards), using its KV store for configuration too means one system serves both jobs, instead of running Eureka/Consul for discovery *and* a separate Spring Cloud Config Server for configuration. The KV store supports the same profile-and-application layering Config Server does — shared defaults, per-application overrides, per-profile overrides — just stored as keys instead of Git files.

Reach for Consul KV config when:

- Consul is already the discovery mechanism, and adding a second system just for configuration would be redundant infrastructure.
- Configuration needs to change frequently and be watched for live updates — Consul's KV store supports blocking queries, so a client can be notified of a change almost immediately rather than polling.
- You want configuration versioned and audited through Consul's own ACLs and audit logging, rather than through Git history.

## 3. Core concept

```
 config/application/data          <- shared defaults, applies to every application
 config/orders-service/data       <- overrides shared defaults, applies to orders-service only
 config/orders-service,prod/data  <- overrides both, applies to orders-service running with "prod" profile

 resolution order (most specific wins):
   application,profile  >  application  >  shared "application"
```

The same layering principle as Spring Cloud Config's Git backend, just expressed as KV path segments instead of file names.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three layers of Consul KV configuration are merged for orders-service running with the prod profile, with more specific keys overriding shared defaults">
  <rect x="220" y="20" width="200" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="41" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">config/application/data</text>

  <rect x="220" y="80" width="200" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="101" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">config/orders-service/data</text>

  <rect x="220" y="140" width="200" height="34" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="161" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">config/orders-service,prod/data</text>

  <line x1="320" y1="54" x2="320" y2="78" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a37)"/>
  <line x1="320" y1="114" x2="320" y2="138" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a37)"/>

  <text x="450" y="41" fill="#8b949e" font-size="7" font-family="sans-serif">shared, lowest priority</text>
  <text x="450" y="101" fill="#8b949e" font-size="7" font-family="sans-serif">app-specific</text>
  <text x="450" y="161" fill="#6db33f" font-size="7" font-family="sans-serif">profile-specific, wins ties</text>

  <defs><marker id="a37" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each layer merges over the one above it, with the most specific (application + profile) layer winning any key conflicts.

## 5. Runnable example

The scenario: resolve `orders-service`'s effective configuration from layered Consul KV entries, starting from a flat single-layer lookup, then adding the application-specific layer, then adding profile-specific overrides with correct merge precedence.

### Level 1 — Basic

A flat KV store — one key path, no layering yet.

```java
import java.util.*;

public class ConsulKvLevel1 {
    static Map<String, String> kv = Map.of(
            "config/application/data", "db.pool.size=10\ntimeout.ms=3000"
    );

    static Map<String, String> parse(String blob) {
        Map<String, String> props = new LinkedHashMap<>();
        for (String line : blob.split("\n")) {
            String[] parts = line.split("=", 2);
            props.put(parts[0], parts[1]);
        }
        return props;
    }

    public static void main(String[] args) {
        Map<String, String> props = parse(kv.get("config/application/data"));
        System.out.println("effective config: " + props);
    }
}
```

How to run: `java ConsulKvLevel1.java`

This is the shared-defaults-only case: every application reading `config/application/data` gets the exact same properties, with no way to override anything per-service yet.

### Level 2 — Intermediate

Add an application-specific layer that overrides the shared defaults.

```java
import java.util.*;

public class ConsulKvLevel2 {
    static Map<String, String> kv = Map.of(
            "config/application/data", "db.pool.size=10\ntimeout.ms=3000",
            "config/orders-service/data", "db.pool.size=25" // overrides just this one key
    );

    static Map<String, String> parse(String blob) {
        Map<String, String> props = new LinkedHashMap<>();
        for (String line : blob.split("\n")) {
            String[] parts = line.split("=", 2);
            props.put(parts[0], parts[1]);
        }
        return props;
    }

    static Map<String, String> resolve(String app) {
        Map<String, String> merged = new LinkedHashMap<>(parse(kv.get("config/application/data")));
        String appKey = "config/" + app + "/data";
        if (kv.containsKey(appKey)) merged.putAll(parse(kv.get(appKey))); // app-specific wins ties
        return merged;
    }

    public static void main(String[] args) {
        System.out.println("orders-service effective config: " + resolve("orders-service"));
    }
}
```

How to run: `java ConsulKvLevel2.java`

`resolve` starts from the shared defaults, then layers the application-specific blob on top with `putAll`, so `db.pool.size` ends up `25` (overridden) while `timeout.ms` stays `3000` (inherited, untouched by the more specific layer) — exactly the merge behavior Consul KV config performs across its layers.

### Level 3 — Advanced

Add the profile-specific layer (`orders-service,prod`) as the most specific override, and resolve for two different profiles to show the same base config diverging correctly.

```java
import java.util.*;

public class ConsulKvLevel3 {
    static Map<String, String> kv = Map.of(
            "config/application/data", "db.pool.size=10\ntimeout.ms=3000\nfeature.new-checkout=false",
            "config/orders-service/data", "db.pool.size=25",
            "config/orders-service,prod/data", "timeout.ms=8000\nfeature.new-checkout=true",
            "config/orders-service,dev/data", "db.pool.size=5"
    );

    static Map<String, String> parse(String blob) {
        Map<String, String> props = new LinkedHashMap<>();
        for (String line : blob.split("\n")) {
            String[] parts = line.split("=", 2);
            props.put(parts[0], parts[1]);
        }
        return props;
    }

    static Map<String, String> resolve(String app, String profile) {
        Map<String, String> merged = new LinkedHashMap<>(parse(kv.get("config/application/data")));
        String appKey = "config/" + app + "/data";
        if (kv.containsKey(appKey)) merged.putAll(parse(kv.get(appKey)));
        String profileKey = "config/" + app + "," + profile + "/data";
        if (kv.containsKey(profileKey)) merged.putAll(parse(kv.get(profileKey))); // most specific, applied last
        return merged;
    }

    public static void main(String[] args) {
        System.out.println("orders-service,prod: " + resolve("orders-service", "prod"));
        System.out.println("orders-service,dev:  " + resolve("orders-service", "dev"));
    }
}
```

How to run: `java ConsulKvLevel3.java`

The `prod` resolution ends with `db.pool.size=25` (from the app layer, untouched by prod), `timeout.ms=8000` and `feature.new-checkout=true` (both overridden by the prod layer). The `dev` resolution instead ends with `db.pool.size=5` (overridden by the dev layer), but `timeout.ms=3000` and `feature.new-checkout=false` fall back to the shared defaults, since the dev layer never mentions them. Same three KV layers of general logic, two completely different effective configurations depending purely on which profile is active.

## 6. Walkthrough

Trace the `resolve("orders-service", "prod")` call in Level 3 step by step.

1. `merged` is initialized from `parse(kv.get("config/application/data"))` — this models the application's `spring.config.import=consul:` machinery first pulling the shared `config/application/data` key, giving a base map of `{db.pool.size=10, timeout.ms=3000, feature.new-checkout=false}`.
2. `appKey` is computed as `"config/orders-service/data"`, found in `kv`, and its parsed contents (`{db.pool.size=25}`) are merged in via `putAll` — this overwrites just the `db.pool.size` entry in `merged`, leaving the other two untouched. This models Spring resolving the application-specific KV path second, per Consul's standard `config/{application}/data` convention.
3. `profileKey` is computed as `"config/orders-service,prod/data"`, found in `kv`, and its contents (`{timeout.ms=8000, feature.new-checkout=true}`) are merged in last — this overwrites those two keys, leaving `db.pool.size` (already `25` from the app layer) untouched, since the prod layer never mentions it.
4. The final `merged` map is `{db.pool.size=25, timeout.ms=8000, feature.new-checkout=true}` — this is exactly what a real Spring Boot app running with `spring.profiles.active=prod` would see in its `Environment`, ready to be injected via `@Value` or bound to a `@ConfigurationProperties` class.
5. The second call, `resolve("orders-service", "dev")`, repeats the same three-step merge but against the `dev` profile key instead, landing on a different `db.pool.size` while `timeout.ms` and `feature.new-checkout` fall through to the shared defaults untouched — demonstrating that each profile only needs to specify what it actually changes.

```
merge order (each step overwrites matching keys from the step before):
  1. config/application/data              (shared defaults)
  2. config/{app}/data                    (app-specific)
  3. config/{app},{profile}/data          (profile-specific, wins any conflict)
```

## 7. Gotchas & takeaways

> **Gotcha:** unlike Spring Cloud Config's Git backend, Consul KV has no built-in commit history browsing UI equivalent to `git log` — changes are visible via Consul's own KV versioning and audit log if ACLs/audit logging are enabled, but reviewing "what changed and why" takes more deliberate setup than a Git-backed Config Server gives for free.

- The `config/{application}[,{profile}]/data` key convention is what makes layering automatic — Spring Cloud Consul Config resolves and merges all applicable keys without any extra code.
- More specific layers are merged last and win ties — shared defaults should hold anything safe for every application and profile; only the differences need to live in the more specific layers.
- Consul KV config supports live updates via blocking queries — combined with `@RefreshScope` (covered earlier under Spring Cloud Config), a KV change can propagate to a running application without a restart, similar to Config Server plus Spring Cloud Bus, but without needing a separate message broker.
- Choosing Consul KV over Config Server's Git backend trades Git's review/audit/rollback workflow for one less system to run — pick based on which tradeoff the team actually values.
