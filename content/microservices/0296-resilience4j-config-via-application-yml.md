---
card: microservices
gi: 296
slug: resilience4j-config-via-application-yml
title: "Resilience4j config via application.yml"
---

## 1. What it is

Resilience4j's Spring Boot integration reads its configuration from `application.yml` (or `.properties`) under the `resilience4j.<module>` prefix, with a `configs` section for shared defaults and an `instances` section for named, per-dependency overrides. This means every threshold, window size, and duration used by `@CircuitBreaker`, `@Retry`, `@Bulkhead`, and the other annotations is externalized configuration, not hardcoded in Java, letting the same code behave differently per environment (dev vs. production) or be re-tuned without a code change and redeploy.

## 2. Why & when

Different downstream dependencies genuinely need different resilience tuning: a fast internal cache lookup might warrant a 200ms timeout and an aggressive circuit breaker, while a slow third-party reporting API might need a 10-second timeout and a much more tolerant failure threshold. Hardcoding these values in Java would mean a code change (and redeploy) every time tuning needs adjusting — often exactly the kind of change an operator wants to make quickly during an incident, without waiting for a full deployment cycle.

Externalizing this to `application.yml` also enables Spring profiles and Spring Cloud Config to vary resilience behavior per environment without touching code at all, and lets the `configs.default` block establish sensible baseline settings that individual `instances` selectively override — avoiding repeating every setting for every single named dependency. Use this approach for essentially all Resilience4j tuning in a Spring Boot application; it is the standard, expected way to configure these modules in Spring, matching how the rest of Spring Boot's externalized configuration works.

## 3. Core concept

`configs.default` establishes shared baseline settings; each entry under `instances` inherits from a named config (or `default` implicitly) and can override specific keys.

```yaml
resilience4j:
  circuitbreaker:
    configs:
      default:                              # shared baseline for ALL instances
        sliding-window-size: 10
        failure-rate-threshold: 50
        wait-duration-in-open-state: 10s
        permitted-number-of-calls-in-half-open-state: 3
    instances:
      inventory:                            # inherits 'default', overrides ONE value
        wait-duration-in-open-state: 5s
      reporting:                            # inherits 'default', overrides TWO values
        failure-rate-threshold: 70
        sliding-window-size: 20
  retry:
    instances:
      inventory:
        max-attempts: 3
        wait-duration: 200ms
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A shared default configuration block establishes baseline settings; each named instance inherits from it and can override specific values, so most configuration is written once in the default block and only the differences are repeated per named instance">
  <rect x="30" y="20" width="220" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">configs.default</text>
  <text x="140" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">shared baseline, written ONCE</text>
  <text x="140" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">e.g. sliding-window-size: 10</text>

  <line x1="140" y1="80" x2="140" y2="100" stroke="#8b949e"/>
  <line x1="140" y1="100" x2="90" y2="115" stroke="#8b949e" marker-end="url(#arr296)"/>
  <line x1="140" y1="100" x2="190" y2="115" stroke="#8b949e" marker-end="url(#arr296)"/>
  <line x1="140" y1="100" x2="290" y2="115" stroke="#8b949e" marker-end="url(#arr296)"/>

  <rect x="30" y="120" width="120" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="141" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">instances.inventory</text>

  <rect x="160" y="120" width="120" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="220" y="141" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">instances.reporting</text>

  <rect x="290" y="120" width="120" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="350" y="141" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">instances.payments</text>

  <defs><marker id="arr296" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each named instance inherits the shared default and layers its own specific overrides on top.

## 5. Runnable example

Scenario: a hardcoded circuit breaker configuration that requires a code change to retune, extended to a config-driven approach that mirrors how Resilience4j's YAML `configs.default` + `instances` resolution works, and finally a small Java resolver that merges a default config map with a named instance's overrides — the exact merge logic Spring's `Resilience4jCircuitBreakerConfigurationProperties` performs internally — demonstrated over multiple named instances at once.

### Level 1 — Basic

```java
// File: HardcodedCircuitBreakerConfig.java -- every threshold is a
// literal value baked into the Java code; changing it requires editing
// this file and redeploying.
public class HardcodedCircuitBreakerConfig {
    static class CircuitBreakerSettings {
        final int slidingWindowSize = 10;      // HARDCODED
        final int failureRateThreshold = 50;   // HARDCODED
        final long waitDurationInOpenStateMs = 10000; // HARDCODED
    }

    public static void main(String[] args) {
        CircuitBreakerSettings inventorySettings = new CircuitBreakerSettings();
        CircuitBreakerSettings reportingSettings = new CircuitBreakerSettings(); // IDENTICAL -- no way to differ without a new class or field
        System.out.println("Inventory: window=" + inventorySettings.slidingWindowSize + " threshold=" + inventorySettings.failureRateThreshold);
        System.out.println("Reporting: window=" + reportingSettings.slidingWindowSize + " threshold=" + reportingSettings.failureRateThreshold);
        System.out.println("To retune 'reporting' differently, this JAVA FILE must be edited and the app redeployed.");
    }
}
```

How to run: `java HardcodedCircuitBreakerConfig.java`

Both `inventorySettings` and `reportingSettings` end up with identical values because they're both instances of the same hardcoded class — there's no way to give one dependency a more tolerant configuration than another without writing more Java code (a subclass, a constructor parameter threaded through everywhere it's used, etc.), and any retuning requires a code change and redeploy.

### Level 2 — Intermediate

```java
// File: ConfigDrivenSettings.java -- settings are loaded from an
// external map (standing in for parsed YAML) rather than hardcoded,
// with each NAMED instance able to differ, mirroring the shape of
// resilience4j.circuitbreaker.instances.<name> in application.yml.
import java.util.Map;

public class ConfigDrivenSettings {
    record CircuitBreakerSettings(int slidingWindowSize, int failureRateThreshold, long waitDurationInOpenStateMs) {}

    // Stands in for YAML parsed under resilience4j.circuitbreaker.instances
    static final Map<String, CircuitBreakerSettings> instanceConfigs = Map.of(
            "inventory", new CircuitBreakerSettings(10, 50, 5000),
            "reporting", new CircuitBreakerSettings(20, 70, 15000)
    );

    static CircuitBreakerSettings resolve(String instanceName) {
        return instanceConfigs.get(instanceName);
    }

    public static void main(String[] args) {
        CircuitBreakerSettings inventory = resolve("inventory");
        CircuitBreakerSettings reporting = resolve("reporting");
        System.out.println("Inventory: " + inventory);
        System.out.println("Reporting: " + reporting);
        System.out.println("Retuning 'reporting' now only requires editing application.yml, no Java changes or redeploy.");
    }
}
```

How to run: `java ConfigDrivenSettings.java`

`inventory` and `reporting` now resolve to genuinely different settings, each defined externally (here, in a `Map` standing in for parsed YAML). In a real Spring Boot app, `Resilience4jCircuitBreakerConfigurationProperties` performs exactly this kind of lookup, binding the `resilience4j.circuitbreaker.instances.*` YAML keys into a settings object per name, with no Java code changes needed to add or retune a named instance.

### Level 3 — Advanced

```java
// File: DefaultPlusOverrideMerge.java -- implements the ACTUAL merge
// logic Resilience4j's Spring configuration binder performs: each named
// instance starts from the shared 'default' config and only its
// EXPLICITLY specified keys override that baseline, matching how
// configs.default + instances.<name> combine in application.yml.
import java.util.*;

public class DefaultPlusOverrideMerge {
    record CircuitBreakerSettings(int slidingWindowSize, int failureRateThreshold, long waitDurationInOpenStateMs) {}

    // configs.default in application.yml
    static final CircuitBreakerSettings DEFAULT = new CircuitBreakerSettings(10, 50, 10000);

    // instances.<name>: OVERRIDES map -- only keys present here differ from default
    static final Map<String, Map<String, Object>> overrides = Map.of(
            "inventory", Map.of("waitDurationInOpenStateMs", 5000L),                              // ONE override
            "reporting", Map.of("failureRateThreshold", 70, "slidingWindowSize", 20),             // TWO overrides
            "payments", Map.of()                                                                   // ZERO overrides -- pure default
    );

    static CircuitBreakerSettings resolve(String instanceName) {
        Map<String, Object> instanceOverrides = overrides.getOrDefault(instanceName, Map.of());
        int slidingWindowSize = (int) instanceOverrides.getOrDefault("slidingWindowSize", DEFAULT.slidingWindowSize());
        int failureRateThreshold = (int) instanceOverrides.getOrDefault("failureRateThreshold", DEFAULT.failureRateThreshold());
        long waitDurationInOpenStateMs = (long) instanceOverrides.getOrDefault("waitDurationInOpenStateMs", DEFAULT.waitDurationInOpenStateMs());
        return new CircuitBreakerSettings(slidingWindowSize, failureRateThreshold, waitDurationInOpenStateMs);
    }

    public static void main(String[] args) {
        for (String name : List.of("inventory", "reporting", "payments")) {
            System.out.println(name + " -> " + resolve(name));
        }
    }
}
```

How to run: `java DefaultPlusOverrideMerge.java`

`payments` has zero overrides and resolves to exactly the `DEFAULT` values. `inventory` overrides only `waitDurationInOpenStateMs`, so its `slidingWindowSize` and `failureRateThreshold` still come from `DEFAULT` while its wait duration is its own. `reporting` overrides two of the three fields — `slidingWindowSize` and `failureRateThreshold` come from its own override map, while `waitDurationInOpenStateMs` falls through to `DEFAULT` since `reporting` never specifies it. This field-by-field merge, where each named instance only needs to specify what's *different* from the shared baseline, is exactly the resolution Spring's Resilience4j configuration binder performs when processing `application.yml`'s `configs.default` plus `instances.<name>` structure.

## 6. Walkthrough

Trace `DefaultPlusOverrideMerge.main`'s resolution of `"reporting"`. **First**, the loop calls `resolve("reporting")`. Inside, `instanceOverrides` is looked up from the `overrides` map, retrieving `Map.of("failureRateThreshold", 70, "slidingWindowSize", 20)` — the two explicitly configured differences for this instance.

**Next**, `slidingWindowSize` is resolved via `instanceOverrides.getOrDefault("slidingWindowSize", DEFAULT.slidingWindowSize())`. Since `"slidingWindowSize"` is present in the overrides map (value `20`), that value wins over the default's `10`.

**`failureRateThreshold` resolves the same way**: present in overrides as `70`, so it wins over the default's `50`.

**`waitDurationInOpenStateMs` resolves differently**: it is *not* present in `reporting`'s overrides map, so `getOrDefault` falls through to `DEFAULT.waitDurationInOpenStateMs()`, which is `10000`.

**The final `CircuitBreakerSettings` for `"reporting"`** is therefore `(slidingWindowSize=20, failureRateThreshold=70, waitDurationInOpenStateMs=10000)` — two fields from its own explicit configuration, one field inherited from the shared default, exactly matching how a YAML block like:
```yaml
resilience4j:
  circuitbreaker:
    configs:
      default: { sliding-window-size: 10, failure-rate-threshold: 50, wait-duration-in-open-state: 10s }
    instances:
      reporting: { failure-rate-threshold: 70, sliding-window-size: 20 }
```
resolves at Spring Boot startup: `reporting`'s bound `CircuitBreakerConfig` ends up with `slidingWindowSize=20`, `failureRateThreshold=70` (from its own block) and `waitDurationInOpenState=10s` (inherited, since `reporting` never mentions it).

**Contrast with `"payments"`**, which has an empty overrides map: every field falls through to `DEFAULT`, producing exactly the baseline settings — this is the value of the default/override pattern, since most dependencies in a real system are fine with sensible shared defaults and only a few need specific tuning.

```
resolve("reporting")
   slidingWindowSize:        override present (20)   -> 20
   failureRateThreshold:     override present (70)   -> 70
   waitDurationInOpenStateMs: override ABSENT         -> falls through to DEFAULT (10000)
```

## 7. Gotchas & takeaways

> An `instances` entry that misspells a key name (e.g., `failure-rate-threshold` written as `failure-rate-threshhold`) is typically silently ignored by Spring's relaxed binding rather than causing a startup error — the instance quietly falls back to that field's default value, which can be confusing to debug since there's no obvious error signal.

- Always define a `configs.default` block with sensible baseline settings, and let individual `instances` override only what genuinely needs to differ — this keeps configuration DRY and makes the differences between dependencies easy to see at a glance.
- YAML duration values (`10s`, `200ms`) are parsed by Spring Boot's relaxed binding into `Duration` objects automatically; this is standard Spring Boot behavior, not something specific to Resilience4j.
- Configuration changes via `application.yml` take effect on the next application restart by default; combining this with Spring Cloud Config and `@RefreshScope` allows some configuration to be updated without a full redeploy, though Resilience4j instance configuration specifically is typically bound once at startup.
- Keep the `name` used in `@CircuitBreaker(name = "...")`, `@Retry(name = "...")`, etc. consistent with the corresponding key under `instances` in `application.yml` — a mismatch silently falls back to the `default` config instead of failing loudly.
