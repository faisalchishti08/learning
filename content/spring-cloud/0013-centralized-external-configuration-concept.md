---
card: spring-cloud
gi: 13
slug: centralized-external-configuration-concept
title: "Centralized external configuration concept"
---

## 1. What it is

Centralized external configuration is the practice of storing every service's configuration outside of, and separately from, the services themselves — in a Git repository, a database, or a secrets vault — and having each service fetch its configuration at startup (or refresh, from the earlier Spring Cloud Context cards) from one central source, rather than each carrying its own bundled `application.yml`.

```
Instead of:
  payment-service.jar  (config baked in at build time)
  inventory-service.jar (config baked in at build time)

Centralized:
  config-repo (Git)
    payment-service.yml
    inventory-service.yml
    application.yml (shared defaults)

  payment-service   --fetches config from--> Config Server --reads from--> config-repo
  inventory-service --fetches config from--> Config Server --reads from--> config-repo
```

## 2. Why & when

This card opens the Spring Cloud Config section, building on the 12-factor principle introduced at the very start of this Spring Cloud coverage: configuration should be externalized from code. Centralization takes that one step further — not just *outside* the application, but in *one shared place* every instance of every service can fetch from, rather than each service instance carrying its own separately-managed config file. This matters enormously once there are dozens of services and many environments (dev, staging, production) — without centralization, keeping configuration consistent and auditable across that whole matrix becomes its own maintenance problem.

Reach for centralized external configuration when:

- Multiple services share configuration values (a shared database connection pool size, a common feature flag) that should change in one place, not be duplicated and independently edited across many service repositories.
- Configuration needs to be auditable and versioned — a Git-backed config repo gives every change a commit history, exactly like application code.
- You want configuration changes to propagate to running instances via the refresh mechanism from earlier cards, without rebuilding or redeploying the actual application artifact.

## 3. Core concept

```
 Per-service bundled config (the OLD way):
   payment-service repo:    src/main/resources/application.yml
   inventory-service repo:   src/main/resources/application.yml
   -- editing a SHARED value means editing it in EVERY service's repo, separately

 Centralized external config (the Spring Cloud Config way):
   config-repo:
     application.yml           -- shared defaults, EVERY service inherits these
     payment-service.yml        -- overrides/additions specific to payment-service
     inventory-service.yml       -- overrides/additions specific to inventory-service

   ONE edit to application.yml in config-repo affects EVERY service that fetches from it.
```

Configuration moves from being bundled per-service to being centrally stored, with a layering model (shared defaults plus per-service overrides) that avoids duplicating common values.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple services each fetch their configuration from one centralized config repository rather than bundling their own">
  <rect x="240" y="20" width="160" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Config Repo (Git)</text>

  <line x1="280" y1="65" x2="120" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a33)"/>
  <line x1="320" y1="65" x2="320" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a33)"/>
  <line x1="360" y1="65" x2="520" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a33)"/>

  <rect x="30" y="105" width="180" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="130" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">payment-service</text>

  <rect x="230" y="105" width="180" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="130" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">inventory-service</text>

  <rect x="430" y="105" width="180" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="130" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">order-service</text>

  <defs><marker id="a33" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every service fetches its configuration from one shared, centrally managed source rather than carrying its own copy.

## 5. Runnable example

The scenario: three services sharing a common database connection setting, evolving from each service bundling its own duplicated copy of that setting, to a centralized source with layered shared-defaults-plus-overrides resolution, to a full simulation showing exactly what happens — a one-line central edit propagating to every service — that duplication makes painful and centralization makes trivial.

### Level 1 — Basic

Show the duplicated-per-service baseline: each service carries its own independent copy of a shared value.

```java
import java.util.*;

public class CentralizedConfigLevel1 {
    public static void main(String[] args) {
        Map<String, String> paymentServiceConfig = new HashMap<>(Map.of("db.pool.size", "10", "service.name", "payment-service"));
        Map<String, String> inventoryServiceConfig = new HashMap<>(Map.of("db.pool.size", "10", "service.name", "inventory-service"));
        Map<String, String> orderServiceConfig = new HashMap<>(Map.of("db.pool.size", "10", "service.name", "order-service"));

        System.out.println("payment-service db.pool.size: " + paymentServiceConfig.get("db.pool.size"));
        System.out.println("inventory-service db.pool.size: " + inventoryServiceConfig.get("db.pool.size"));
        System.out.println("order-service db.pool.size: " + orderServiceConfig.get("db.pool.size"));
        // db.pool.size = 10 is duplicated THREE times -- changing it means editing THREE separate places.
    }
}
```

How to run: `java CentralizedConfigLevel1.java`

`db.pool.size` is copy-pasted into all three configs — a genuinely shared value that, if it needs to change, requires three separate, easy-to-miss edits, one per service.

### Level 2 — Intermediate

Add a centralized config source with a layered resolution: a shared `application` defaults map, plus a per-service overrides map, merged together.

```java
import java.util.*;

public class CentralizedConfigLevel2 {
    public static void main(String[] args) {
        ConfigRepo repo = new ConfigRepo();
        repo.setSharedDefaults(Map.of("db.pool.size", "10"));
        repo.setServiceOverrides("payment-service", Map.of("service.name", "payment-service"));
        repo.setServiceOverrides("inventory-service", Map.of("service.name", "inventory-service"));
        repo.setServiceOverrides("order-service", Map.of("service.name", "order-service"));

        for (String serviceId : List.of("payment-service", "inventory-service", "order-service")) {
            Map<String, String> resolved = repo.resolveConfigFor(serviceId);
            System.out.println(serviceId + " -> db.pool.size=" + resolved.get("db.pool.size"));
        }
    }
}

// Stands in for a Config Server reading layered configuration from a shared config repository.
class ConfigRepo {
    private Map<String, String> sharedDefaults = Map.of();
    private final Map<String, Map<String, String>> serviceOverrides = new HashMap<>();

    void setSharedDefaults(Map<String, String> defaults) { this.sharedDefaults = defaults; }
    void setServiceOverrides(String serviceId, Map<String, String> overrides) { serviceOverrides.put(serviceId, overrides); }

    Map<String, String> resolveConfigFor(String serviceId) {
        Map<String, String> resolved = new HashMap<>(sharedDefaults); // start from shared
        resolved.putAll(serviceOverrides.getOrDefault(serviceId, Map.of())); // layer service-specific on top
        return resolved;
    }
}
```

How to run: `java CentralizedConfigLevel2.java`

`db.pool.size` exists in exactly one place — `sharedDefaults` — and every service's resolved config inherits it automatically via `resolveConfigFor`; per-service overrides only carry what's genuinely specific to that service.

### Level 3 — Advanced

Show the actual payoff explicitly: changing the centralized shared default once, and confirming every service picks up the new value on its next config fetch, with no per-service edits needed at all.

```java
import java.util.*;

public class CentralizedConfigLevel3 {
    public static void main(String[] args) {
        ConfigRepo repo = new ConfigRepo();
        repo.setSharedDefaults(Map.of("db.pool.size", "10"));
        repo.setServiceOverrides("payment-service", Map.of("service.name", "payment-service"));
        repo.setServiceOverrides("inventory-service", Map.of("service.name", "inventory-service"));
        repo.setServiceOverrides("order-service", Map.of("service.name", "order-service"));

        List<String> services = List.of("payment-service", "inventory-service", "order-service");

        System.out.println("--- Before central change ---");
        for (String serviceId : services) printResolved(repo, serviceId);

        // ONE edit, in ONE place -- the central repo's shared defaults.
        repo.setSharedDefaults(Map.of("db.pool.size", "50")); // traffic grew, pool size needs to increase

        System.out.println("--- After central change (each service re-fetches on its next refresh) ---");
        for (String serviceId : services) printResolved(repo, serviceId);
    }

    static void printResolved(ConfigRepo repo, String serviceId) {
        Map<String, String> resolved = repo.resolveConfigFor(serviceId);
        System.out.println(serviceId + " -> db.pool.size=" + resolved.get("db.pool.size"));
    }
}

class ConfigRepo {
    private Map<String, String> sharedDefaults = Map.of();
    private final Map<String, Map<String, String>> serviceOverrides = new HashMap<>();
    void setSharedDefaults(Map<String, String> defaults) { this.sharedDefaults = defaults; }
    void setServiceOverrides(String serviceId, Map<String, String> overrides) { serviceOverrides.put(serviceId, overrides); }
    Map<String, String> resolveConfigFor(String serviceId) {
        Map<String, String> resolved = new HashMap<>(sharedDefaults);
        resolved.putAll(serviceOverrides.getOrDefault(serviceId, Map.of()));
        return resolved;
    }
}
```

How to run: `java CentralizedConfigLevel3.java`

`repo.setSharedDefaults(...)` is called exactly once to change `db.pool.size` from `10` to `50` — no per-service code or config is touched at all — and the second `for` loop, calling the *exact same* `printResolved` against the *exact same* three service ids, reflects the new value for every one of them automatically.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three services' configs are resolved and printed against the initial shared default of `10`:

```
--- Before central change ---
payment-service -> db.pool.size=10
inventory-service -> db.pool.size=10
order-service -> db.pool.size=10
```

`repo.setSharedDefaults(Map.of("db.pool.size", "50"))` replaces the central shared-defaults map — this single call is the equivalent of a single commit to a config repository's `application.yml` in a real Spring Cloud Config setup. The second loop calls `resolveConfigFor` again for each service, and since `resolveConfigFor` always starts fresh from whatever `sharedDefaults` currently is:

```
--- After central change (each service re-fetches on its next refresh) ---
payment-service -> db.pool.size=50
inventory-service -> db.pool.size=50
order-service -> db.pool.size=50
```

In a real deployment, this single commit to the config repository is picked up by each running service instance the next time it fetches configuration — either at its own next restart, or live via the `/actuator/refresh` mechanism from the earlier Spring Cloud Context cards, without rebuilding or redeploying any service's actual application artifact. The next card introduces the actual Config Server component that serves this centralized configuration over HTTP to every requesting service.

## 7. Gotchas & takeaways

> Gotcha: centralizing configuration also centralizes the *blast radius* of a mistake — a typo in a shared default that every service inherits can break every service simultaneously, unlike a per-service config error that would previously have only affected one service; the auditability and change-review discipline a Git-backed config repo enables becomes correspondingly more important, not less.

> Gotcha: "centralized" doesn't mean "one flat file for everything" — the shared-defaults-plus-per-service-overrides layering shown here (formalized by Spring Cloud Config's actual file-naming conventions in the next several cards) is what keeps centralization from turning into an unmanageable single file mixing every service's unrelated settings together.

- Centralized external configuration stores every service's config in one shared location, rather than bundled independently per service, so shared values are edited once instead of duplicated across many repositories.
- A layered model — shared defaults plus per-service overrides — avoids both duplication of common values and a single unmanageable file mixing unrelated settings.
- Centralizing configuration also centralizes risk: a mistake in shared defaults affects every dependent service at once, making change review and auditability more important, not less.
- The next card introduces Spring Cloud Config Server, the actual component that serves this centralized configuration over HTTP to requesting services.
