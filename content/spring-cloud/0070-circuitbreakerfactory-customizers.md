---
card: spring-cloud
gi: 70
slug: circuitbreakerfactory-customizers
title: "CircuitBreakerFactory & customizers"
---

## 1. What it is

`Customizer<CircuitBreakerFactory>` (specifically `Resilience4JCircuitBreakerFactory` for Resilience4j) is a bean that lets you configure per-instance circuit breaker behavior in Java code rather than (or in addition to) properties — useful for configuration that properties alone can't express, like default fallback behavior applied across every circuit breaker the factory creates, or genuinely dynamic, computed configuration.

```java
@Bean
Customizer<Resilience4JCircuitBreakerFactory> defaultCustomizer() {
    return factory -> factory.configureDefault(id -> new Resilience4JConfigBuilder(id)
            .circuitBreakerConfig(CircuitBreakerConfig.custom()
                    .slidingWindowSize(10)
                    .failureRateThreshold(50)
                    .build())
            .timeLimiterConfig(TimeLimiterConfig.custom()
                    .timeoutDuration(Duration.ofSeconds(3))
                    .build())
            .build());
}

@Bean
Customizer<Resilience4JCircuitBreakerFactory> billingServiceCustomizer() {
    return factory -> factory.configure(builder -> builder
            .circuitBreakerConfig(CircuitBreakerConfig.custom().failureRateThreshold(30).build()),
            "billing-service"); // override JUST for this one instance
}
```

## 2. Why & when

Properties (`resilience4j.circuitbreaker.instances.*`) cover the overwhelming majority of configuration needs declaratively, but some things genuinely need code: a *default* configuration applied to every circuit breaker the factory ever creates (so new instances automatically get sane defaults without needing an explicit properties entry each time), configuration values computed at startup from something other than a static property, or programmatic registration of many instances from a dynamic list (echoing the Route Metadata card's Java-DSL-vs-YAML tradeoff from the earlier section).

Reach for `Customizer<CircuitBreakerFactory>` when:

- Every circuit breaker instance in the application should share a sensible default configuration, and only a few specific ones need overrides — `configureDefault` plus targeted `configure(..., "specific-name")` calls express this cleanly.
- Configuration needs to be computed rather than statically declared — reading from a database, deriving a threshold from an environment-specific calculation, or generating instances from a dynamic list of downstream services.
- You want Resilience4j-specific configuration objects (`CircuitBreakerConfig`, `TimeLimiterConfig`) with their full builder API, which offers more detail and type safety than flat property keys alone.

## 3. Core concept

```
 Customizer<Resilience4JCircuitBreakerFactory>:

   factory.configureDefault(id -> ...)       <- applies to EVERY instance, used as a fallback baseline
   factory.configure(builder -> ..., "name") <- overrides configuration for ONE specific named instance

 resolution for a given instance name:
   specific configure(..., name) if one was registered for it
   otherwise falls back to configureDefault(...)
```

Defaults establish a baseline every instance inherits; specific overrides selectively deviate from that baseline where actually needed.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Every circuit breaker instance inherits the configured default unless a specific override was registered for its exact name, in which case the override takes precedence" >
  <rect x="230" y="20" width="180" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">configureDefault(...)</text>
  <text x="320" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">baseline for every instance</text>

  <rect x="30" y="110" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="120" y="132" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">promotions-service</text>
  <text x="120" y="148" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">no override -&gt; uses default</text>

  <rect x="430" y="110" width="180" height="50" rx="8" fill="#1c2430" stroke="#e64949" stroke-width="1.3"/>
  <text x="520" y="132" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billing-service</text>
  <text x="520" y="148" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">has its own configure(...) override</text>

  <line x1="290" y1="70" x2="150" y2="108" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a70)"/>
  <line x1="350" y1="70" x2="490" y2="108" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <defs><marker id="a70" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Only instances with an explicit override deviate from the shared default — everything else inherits it automatically.

## 5. Runnable example

The scenario: configure circuit breakers for `billing-service` and `promotions-service` using a default-plus-overrides model. Start with per-instance configuration only (repetitive), then add a shared default, then add a specific override for one instance that needs different behavior.

### Level 1 — Basic

Per-instance configuration only, repeated for every single service — the redundancy a default eliminates.

```java
import java.util.*;

public class CustomizerLevel1 {
    record CircuitBreakerConfig(int slidingWindowSize, double failureRateThreshold) {}

    static Map<String, CircuitBreakerConfig> configs = new HashMap<>();

    static void configure(String name, int windowSize, double threshold) {
        configs.put(name, new CircuitBreakerConfig(windowSize, threshold));
    }

    public static void main(String[] args) {
        // every single service repeats the same baseline values, even when they don't actually differ
        configure("billing-service", 10, 50);
        configure("promotions-service", 10, 50);
        configure("inventory-service", 10, 50);

        System.out.println(configs);
    }
}
```

How to run: `java CustomizerLevel1.java`

Three services, three identical calls repeating the exact same values — fine for three services, tedious and error-prone (a typo in one repetition, a forgotten fourth service) at real-world scale.

### Level 2 — Intermediate

Add a default configuration, used automatically by any instance without an explicit override.

```java
import java.util.*;
import java.util.function.Supplier;

public class CustomizerLevel2 {
    record CircuitBreakerConfig(int slidingWindowSize, double failureRateThreshold) {}

    static CircuitBreakerConfig defaultConfig;
    static Map<String, CircuitBreakerConfig> overrides = new HashMap<>();

    static void configureDefault(CircuitBreakerConfig config) { defaultConfig = config; }
    static void configure(String name, CircuitBreakerConfig config) { overrides.put(name, config); }

    static CircuitBreakerConfig resolve(String name) {
        return overrides.getOrDefault(name, defaultConfig); // specific override wins, else fall back to default
    }

    public static void main(String[] args) {
        configureDefault(new CircuitBreakerConfig(10, 50));

        // no per-service calls needed at all -- every service just inherits the default automatically
        for (String service : List.of("billing-service", "promotions-service", "inventory-service")) {
            System.out.println(service + " -> " + resolve(service));
        }
    }
}
```

How to run: `java CustomizerLevel2.java`

`resolve` checks `overrides` first, falling back to `defaultConfig` — with no overrides registered at all, every one of the three services correctly resolves to the same default configuration, without a single repetitive per-service call being needed.

### Level 3 — Advanced

Add a specific override for `billing-service` (which genuinely needs stricter behavior — perhaps it's a more critical, latency-sensitive dependency), while every other service continues inheriting the shared default unchanged.

```java
import java.util.*;

public class CustomizerLevel3 {
    record CircuitBreakerConfig(int slidingWindowSize, double failureRateThreshold, int timeoutSeconds) {}

    static CircuitBreakerConfig defaultConfig;
    static Map<String, CircuitBreakerConfig> overrides = new HashMap<>();

    static void configureDefault(CircuitBreakerConfig config) { defaultConfig = config; }
    static void configure(String name, CircuitBreakerConfig config) { overrides.put(name, config); }

    static CircuitBreakerConfig resolve(String name) {
        return overrides.getOrDefault(name, defaultConfig);
    }

    public static void main(String[] args) {
        // baseline, applied to every instance unless overridden
        configureDefault(new CircuitBreakerConfig(10, 50, 3));

        // billing-service is critical and latency-sensitive -- stricter threshold, shorter timeout
        configure("billing-service", new CircuitBreakerConfig(20, 30, 1));

        for (String service : List.of("billing-service", "promotions-service", "inventory-service")) {
            System.out.println(service + " -> " + resolve(service));
        }
    }
}
```

How to run: `java CustomizerLevel3.java`

`billing-service` resolves to its own explicitly registered override — a larger window (`20`), a stricter failure threshold (`30%` instead of `50%`), and a shorter timeout (`1` second instead of `3`) — reflecting that it's judged more critical and latency-sensitive than the other services. `promotions-service` and `inventory-service`, having no override registered for their names, both resolve to the exact same shared default, with zero repetitive configuration needed for either of them.

## 6. Walkthrough

Trace the `resolve` calls in Level 3.

1. `configureDefault(new CircuitBreakerConfig(10, 50, 3))` runs first, setting the baseline every unconfigured instance will inherit — this models a `Customizer<Resilience4JCircuitBreakerFactory>` bean's `factory.configureDefault(...)` call, applied once at application startup.
2. `configure("billing-service", new CircuitBreakerConfig(20, 30, 1))` runs next, registering a specific override keyed to the exact name `"billing-service"` — this models a *second*, separate `Customizer` bean's `factory.configure(..., "billing-service")` call, deliberately narrower in scope than the default.
3. The loop calls `resolve("billing-service")` first — `overrides.getOrDefault("billing-service", defaultConfig)` finds the exact key present in `overrides`, so it returns the override configuration directly, bypassing `defaultConfig` entirely.
4. `resolve("promotions-service")` runs next — `overrides` has no entry for this exact name, so `getOrDefault` falls through to its second argument, returning `defaultConfig` unchanged.
5. `resolve("inventory-service")` runs last, with the identical outcome to `promotions-service` — no override registered, so it inherits the shared default.
6. The three printed lines show the resolution working exactly as intended: one deliberately-configured exception (`billing-service`), and every other service automatically and correctly inheriting the shared baseline without any explicit per-service configuration having been written for them.

```
configureDefault -> baseline: {window=10, threshold=50%, timeout=3s}
configure("billing-service", ...) -> override: {window=20, threshold=30%, timeout=1s}

resolve("billing-service")     -> override found -> {20, 30%, 1s}
resolve("promotions-service")  -> no override -> falls back to default -> {10, 50%, 3s}
resolve("inventory-service")   -> no override -> falls back to default -> {10, 50%, 3s}
```

## 7. Gotchas & takeaways

> **Gotcha:** registering multiple `Customizer<Resilience4JCircuitBreakerFactory>` beans that each call `configureDefault` (rather than one bean calling it once, with others only calling `configure` for specific overrides) can produce confusing "which default actually won" behavior, since Spring applies all matching `Customizer` beans, and the last one to run for a given configuration key wins. Keep exactly one `configureDefault` call across the whole application, and use targeted `configure(..., "name")` calls for every actual override, to keep configuration precedence unambiguous.

- `configureDefault` establishes a baseline every circuit breaker instance inherits automatically, eliminating the need to repeat identical configuration for every service that doesn't actually need anything different.
- `configure(..., "specific-name")` overrides that baseline for exactly the named instance, leaving every other instance's resolution untouched — the standard pattern for the handful of services that genuinely need different tuning.
- This default-plus-targeted-override pattern mirrors the earlier route-metadata and configuration-layering cards (Consul KV config's layered resolution, for instance) — recognizing the recurring shape (baseline plus selective overrides, most specific wins) makes it faster to apply correctly here too.
- Reach for `Customizer` beans specifically when properties alone can't express what's needed — a shared programmatic default, computed configuration, or Resilience4j's full builder API — and prefer plain properties for anything that's simple, static, and doesn't need that flexibility.
