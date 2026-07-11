---
card: spring-cloud
gi: 6
slug: spring-cloud-context-lifecycle-refresh
title: "Spring Cloud Context (lifecycle, refresh)"
---

## 1. What it is

Spring Cloud Context provides the utility beans and events (`ContextRefresher`, `RefreshScope`, `EnvironmentChangeEvent`) that let a running Spring application's configuration change *without a restart* — re-reading property sources and selectively re-creating just the beans that depend on the changed values.

```java
@Autowired ContextRefresher contextRefresher;

Set<String> changedKeys = contextRefresher.refresh(); // re-reads property sources, publishes change events
```

## 2. Why & when

A normal Spring Boot application reads its configuration once, at startup, and that's it — changing a property means restarting the process. In a distributed system with many running instances, restarting every instance just to pick up a config change (a feature flag flip, an updated rate limit) is disruptive and slow. Spring Cloud Context provides the machinery to refresh configuration live, in a running process, safely limiting which beans actually get recreated.

Reach for Spring Cloud Context's refresh mechanism when:

- Configuration needs to change at runtime without restarting the application — feature flags, rate limits, externally-tunable thresholds.
- You're using a Config Server (or any dynamic property source) and want changes there to propagate to running instances without a redeploy.
- You need fine control over *which* beans actually respond to a config change, rather than requiring the entire application to be rebuilt.

## 3. Core concept

```
 Config value changes at the source (e.g. a Config Server's backing Git repo)

 POST /actuator/refresh   (or a scheduled/event-driven trigger)
   -> ContextRefresher re-reads all property sources
   -> compares old vs. new values -> computes the SET of changed keys
   -> publishes EnvironmentChangeEvent with those changed keys
   -> any bean in a @RefreshScope (next card) whose config depends on a changed key
        is DESTROYED and lazily RE-CREATED on next use, picking up the new value

 Beans NOT in @RefreshScope are untouched -- they keep whatever value they read at original startup.
```

Refresh is selective: only refresh-scoped beans respond to a change; everything else in the application keeps running with its original, startup-time configuration.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A refresh event re-reads properties and recreates only refresh-scoped beans while leaving other beans untouched">
  <rect x="20" y="20" width="220" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">POST /actuator/refresh</text>

  <line x1="130" y1="60" x2="130" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a27)"/>

  <rect x="20" y="95" width="220" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="120" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">re-read properties, diff changes</text>

  <line x1="240" y1="115" x2="330" y2="80" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a27)"/>
  <line x1="240" y1="115" x2="330" y2="150" stroke="#79c0ff" stroke-width="1.3" marker-end="url(#a27)"/>

  <rect x="340" y="55" width="260" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="80" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">@RefreshScope beans: recreated</text>

  <rect x="340" y="130" width="260" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="155" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Other beans: untouched</text>

  <defs><marker id="a27" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A refresh selectively recreates refresh-scoped beans while leaving every other bean as it was.

## 5. Runnable example

The scenario: a service reading a runtime-tunable rate limit, evolving from a value fixed permanently at startup (requiring a restart to change), to a refreshable value that updates when a refresh is triggered, to a full simulation showing exactly which beans respond to a refresh and which don't — mirroring `@RefreshScope`'s selective behavior.

### Level 1 — Basic

Show the fixed-at-startup baseline: a value read once, with no way to change it without restarting.

```java
public class ContextRefreshLevel1 {
    public static void main(String[] args) {
        RateLimiter limiter = new RateLimiter(readProperty("rate.limit.perMinute")); // fixed FOREVER at construction
        System.out.println("Rate limit: " + limiter.limit);

        // Even if the underlying property source changes NOW, this running RateLimiter never finds out.
        System.out.println("(property source changes, but this instance can't see it without a restart)");
    }

    static int readProperty(String key) { return 100; } // stands in for reading application.yml at startup
}

class RateLimiter {
    final int limit;
    RateLimiter(int limit) { this.limit = limit; }
}
```

How to run: `java ContextRefreshLevel1.java`

`RateLimiter.limit` is fixed the instant the object is constructed — no mechanism exists for it to ever change again short of destroying and recreating the whole process.

### Level 2 — Intermediate

Add a refreshable value: a property source that can change, and a component that re-reads it when explicitly told to refresh.

```java
import java.util.*;

public class ContextRefreshLevel2 {
    public static void main(String[] args) {
        PropertySource propertySource = new PropertySource();
        propertySource.set("rate.limit.perMinute", "100");

        RefreshableRateLimiter limiter = new RefreshableRateLimiter(propertySource);
        System.out.println("Initial rate limit: " + limiter.currentLimit());

        propertySource.set("rate.limit.perMinute", "250"); // config changes at the source
        System.out.println("Before refresh (stale): " + limiter.currentLimit()); // still cached? depends on design

        ContextRefresher refresher = new ContextRefresher(propertySource);
        Set<String> changedKeys = refresher.refresh();
        System.out.println("Refreshed, changed keys: " + changedKeys);
        System.out.println("After refresh: " + limiter.currentLimit());
    }
}

class PropertySource {
    private final Map<String, String> values = new HashMap<>();
    void set(String key, String value) { values.put(key, value); }
    String get(String key) { return values.get(key); }
}

// Reads the property source FRESH on every call -- mirrors an @RefreshScope bean's lazy re-creation behavior.
class RefreshableRateLimiter {
    private final PropertySource propertySource;
    RefreshableRateLimiter(PropertySource propertySource) { this.propertySource = propertySource; }
    int currentLimit() { return Integer.parseInt(propertySource.get("rate.limit.perMinute")); }
}

class ContextRefresher {
    private final PropertySource propertySource;
    ContextRefresher(PropertySource propertySource) { this.propertySource = propertySource; }
    Set<String> refresh() { return Set.of("rate.limit.perMinute"); } // simplified: reports what changed
}
```

How to run: `java ContextRefreshLevel2.java`

`RefreshableRateLimiter.currentLimit()` re-reads `propertySource` on every call rather than caching the value at construction — so it reflects the new `250` limit immediately, without any explicit "refresh" step needed on its own part; the `ContextRefresher.refresh()` call here mainly reports which keys changed, useful for beans that *do* cache and need to know when to invalidate.

### Level 3 — Advanced

Show the selective-refresh behavior explicitly: one bean marked as refresh-scoped (recreated on refresh) alongside another that isn't (stays stale forever) — the actual distinction `@RefreshScope` draws.

```java
import java.util.*;

public class ContextRefreshLevel3 {
    public static void main(String[] args) {
        PropertySource propertySource = new PropertySource();
        propertySource.set("rate.limit.perMinute", "100");

        // A "singleton-scoped" style bean: caches its value permanently at creation.
        PlainRateLimiter plainLimiter = new PlainRateLimiter(propertySource);
        // A "@RefreshScope" style bean: managed by a scope that can destroy and recreate it.
        RefreshScopeHolder<RefreshScopedRateLimiter> refreshScopedLimiter =
            new RefreshScopeHolder<>(() -> new RefreshScopedRateLimiter(propertySource));

        System.out.println("Before change:");
        System.out.println("  plain: " + plainLimiter.limit);
        System.out.println("  refresh-scoped: " + refreshScopedLimiter.get().limit);

        propertySource.set("rate.limit.perMinute", "250"); // config source changes

        System.out.println("After property change, BEFORE refresh:");
        System.out.println("  plain: " + plainLimiter.limit); // never changes -- constructed once, forever
        System.out.println("  refresh-scoped: " + refreshScopedLimiter.get().limit); // still cached instance, still old

        refreshScopedLimiter.invalidate(); // simulates the @RefreshScope proxy destroying its cached instance

        System.out.println("After refresh:");
        System.out.println("  plain: " + plainLimiter.limit); // STILL never changes
        System.out.println("  refresh-scoped: " + refreshScopedLimiter.get().limit); // recreated, reads NEW value
    }
}

class PropertySource {
    private final Map<String, String> values = new HashMap<>();
    void set(String key, String value) { values.put(key, value); }
    String get(String key) { return values.get(key); }
}

class PlainRateLimiter {
    final int limit;
    PlainRateLimiter(PropertySource propertySource) { this.limit = Integer.parseInt(propertySource.get("rate.limit.perMinute")); }
}

class RefreshScopedRateLimiter {
    final int limit;
    RefreshScopedRateLimiter(PropertySource propertySource) { this.limit = Integer.parseInt(propertySource.get("rate.limit.perMinute")); }
}

// Stands in for Spring's @RefreshScope proxy: holds a cached instance, but can be told to invalidate and recreate it.
class RefreshScopeHolder<T> {
    private final java.util.function.Supplier<T> factory;
    private T cached;
    RefreshScopeHolder(java.util.function.Supplier<T> factory) { this.factory = factory; this.cached = factory.get(); }
    T get() { return cached; }
    void invalidate() { cached = factory.get(); } // destroy and lazily recreate -- exactly what a refresh event triggers
}
```

How to run: `java ContextRefreshLevel3.java`

`plainLimiter.limit` is a plain `final int`, read once at construction and never touched again — it stays `100` for the rest of the program's life regardless of what happens to `propertySource`. `refreshScopedLimiter` behaves the same way *until* `invalidate()` is called — mirroring how `@RefreshScope` doesn't magically make a bean reactive to change; a refresh event explicitly triggers the scope to discard its cached instance so the next access constructs a fresh one against current property values.

## 6. Walkthrough

Execution starts in `main` for Level 3. Both limiters are constructed while `rate.limit.perMinute = 100`, so both read `100` initially:

```
Before change:
  plain: 100
  refresh-scoped: 100
```

`propertySource.set(...)` changes the underlying value to `250`, but neither limiter notices yet — `plainLimiter.limit` is a fixed field, and `refreshScopedLimiter.get()` still returns the same cached `RefreshScopedRateLimiter` instance constructed earlier:

```
After property change, BEFORE refresh:
  plain: 100
  refresh-scoped: 100
```

`refreshScopedLimiter.invalidate()` discards the cached instance and calls `factory.get()` again, constructing a brand-new `RefreshScopedRateLimiter` that reads `propertySource` fresh — picking up `250` this time. `plainLimiter` is entirely unaffected, since nothing about `invalidate()` touches it:

```
After refresh:
  plain: 100
  refresh-scoped: 250
```

In a real Spring Cloud application, `@RefreshScope`'s actual mechanism (the next card) is a scope-aware proxy that Spring's `ContextRefresher` tells to discard its cached target bean whenever a relevant `EnvironmentChangeEvent` fires — every subsequent method call on the proxy transparently triggers lazy re-creation against the now-current `Environment`, exactly as `invalidate()`-then-`get()` does here.

## 7. Gotchas & takeaways

> Gotcha: a refresh only affects beans explicitly annotated `@RefreshScope` (or components that manually re-read configuration, like `RefreshableRateLimiter` in Level 2) — every other singleton-scoped bean in the application, including ones that indirectly used a now-stale config value during their own construction, keeps whatever it had at startup, silently, until the process actually restarts.

> Gotcha: recreating a `@RefreshScope` bean re-runs its constructor and `@PostConstruct` logic — a refresh-scoped bean with expensive initialization (opening a connection, warming a cache) pays that cost again on every refresh, not just at application startup, which matters if refreshes happen frequently.

- Spring Cloud Context provides the machinery (`ContextRefresher`, `EnvironmentChangeEvent`) for live configuration updates without a full application restart.
- A refresh re-reads all property sources and computes which keys actually changed, then notifies the parts of the application that care.
- Only refresh-scoped beans (the next card's `@RefreshScope`) respond automatically — everything else keeps its startup-time configuration until the process restarts.
- Recreating a refresh-scoped bean re-runs its full initialization, which matters for beans with expensive setup logic.
