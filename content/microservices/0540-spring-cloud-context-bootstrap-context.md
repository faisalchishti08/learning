---
card: microservices
gi: 540
slug: spring-cloud-context-bootstrap-context
title: "Spring Cloud Context (bootstrap context)"
---

## 1. What it is

**Spring Cloud Context** provides the utility beans and mechanisms that most other Spring Cloud modules build on: `@RefreshScope` (beans that can be re-created on demand to pick up updated configuration), the `/actuator/refresh` endpoint, and — in older Spring Cloud versions — a separate **bootstrap context**, a parent Spring context created before the main application context specifically to load configuration from an external source (like Spring Cloud Config Server) before anything else in the application starts. In current Spring Cloud versions, the bootstrap context is disabled by default in favor of Spring Boot's own regular configuration import mechanism (`spring.config.import`), but understanding what it did (and why it existed) explains a lot of how `@RefreshScope` and Config Client integration actually work.

## 2. Why & when

You need to understand the bootstrap context (or its modern replacement) because configuration retrieved from an external source has a fundamentally different timing requirement than configuration baked into a local `application.yml`:

- **External configuration needs to be fetched *before* most of the application context is created**, since beans throughout the application may depend on property values that only Config Server can supply (a database URL, a feature flag, credentials). If this fetch happened only as part of normal context initialization, ordering problems could arise — beans needing these properties might be created before the properties are actually available.
- **The (legacy) bootstrap context solved this by running as a separate, earlier-loading parent context**, specifically responsible for talking to Config Server and populating a `PropertySource` that the main application context could then rely on being present from the very start of its own initialization.
- **Modern Spring Cloud (2020.0+) replaced this with `spring.config.import=optional:configserver:`**, using Spring Boot's own standard configuration-import mechanism instead of a separate bootstrap context — simpler, avoiding an entire extra context's startup overhead and complexity, while achieving the same "fetch external config before the rest of the application needs it" goal.
- **`@RefreshScope` is the part of Spring Cloud Context that persists regardless of which mechanism fetched the initial configuration** — it's what allows specific beans to be torn down and recreated on demand (triggered by `/actuator/refresh` or, fleet-wide, by [Spring Cloud Bus](0537-spring-cloud-bus-for-cross-instance-coordination.md)), re-evaluating their `@Value`-bound fields against whatever the current configuration now says.

## 3. Core concept

Think of a theater production that needs its script finalized and delivered to every actor *before* rehearsals for the actual performance can meaningfully begin — you wouldn't want actors improvising their lines because the final script arrived mid-rehearsal. The bootstrap context (or its modern `spring.config.import` replacement) is that "get the script first" step: a dedicated phase specifically for retrieving externally-sourced configuration, completed before the rest of the application's beans (the "actors") are wired up and start relying on values from that script. `@RefreshScope`, separately, is like giving specific actors a way to receive an updated script mid-run and adjust their performance from that point forward, without restarting the entire show from scratch.

Concretely:

1. **Legacy behavior**: a separate bootstrap `ApplicationContext` was created first, specifically to process `bootstrap.yml`/`bootstrap.properties` and talk to Config Server, becoming the parent context of the main application context — guaranteeing config was available before the main context's beans were created.
2. **Modern behavior (Spring Cloud 2020.0+, the current default)**: no separate bootstrap context; instead, `spring.config.import=optional:configserver:http://localhost:8888` in the regular `application.yml` tells Spring Boot's own configuration-loading machinery to fetch from Config Server as one more configuration source, resolved early in the single application context's own startup sequence.
3. **`@RefreshScope` on a bean** means that bean isn't a normal eagerly-created singleton — it's wrapped in a special proxy that can be invalidated and lazily recreated, re-reading its `@Value`/`@ConfigurationProperties` bindings against the current Environment the next time it's accessed after a refresh.
4. **`/actuator/refresh`** (or, fleet-wide, `/actuator/busrefresh` via [Spring Cloud Bus](0537-spring-cloud-bus-for-cross-instance-coordination.md)) triggers exactly this invalidation for every `@RefreshScope` bean, causing them to be recreated with fresh configuration values on their next access.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Legacy: a separate bootstrap context fetches external config before the main context starts. Modern: spring.config.import fetches it as part of the single application context's own startup">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Legacy: bootstrap context</text>
  <rect x="20" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">bootstrap context: fetch config first</text>
  <rect x="20" y="75" width="260" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="150" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">main context: created AFTER, as child</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Modern: config import</text>
  <rect x="380" y="35" width="260" height="70" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="58" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ONE application context</text>
  <text x="510" y="76" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">spring.config.import=configserver:...</text>
  <text x="510" y="94" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">resolved early in normal startup</text>
</svg>

The legacy bootstrap context and the modern config-import mechanism both guarantee external config loads before the rest of the application depends on it, but the modern approach avoids a separate context entirely.

## 5. Runnable example

Scenario: a bean whose behavior depends on a configuration value that needs to be refreshable at runtime. We start with a plain Java model of a value bound once at startup (showing the staleness problem), extend it to a refreshable version, then show the real `@RefreshScope` shape.

### Level 1 — Basic

```java
// File: BoundOnceAtStartup.java -- models a value bound ONCE, at
// construction time -- it never changes again, even if the underlying
// "configuration" changes later.
public class BoundOnceAtStartup {
    static class FeatureFlagHolder {
        private final boolean enabled;
        FeatureFlagHolder(boolean enabled) { this.enabled = enabled; } // bound ONCE, at construction
        boolean isEnabled() { return enabled; }
    }

    public static void main(String[] args) {
        boolean currentConfigValue = false;
        FeatureFlagHolder holder = new FeatureFlagHolder(currentConfigValue);
        System.out.println("Initial: " + holder.isEnabled());

        currentConfigValue = true; // "configuration" changes...
        System.out.println("After config change: " + holder.isEnabled() + " -- STALE! holder never re-reads the new value.");
    }
}
```

How to run: `java BoundOnceAtStartup.java`

`FeatureFlagHolder`'s `enabled` field is set once in the constructor and never re-evaluated — changing `currentConfigValue` afterward has no effect on the already-constructed `holder`, demonstrating exactly the staleness problem `@RefreshScope` exists to solve for real Spring beans.

### Level 2 — Intermediate

```java
// File: RefreshableHolder.java -- models the REFRESH idea: a holder that
// can be explicitly told to RE-READ the current configuration value on demand.
import java.util.function.Supplier;

public class RefreshableHolder {
    static class RefreshableFeatureFlagHolder {
        private final Supplier<Boolean> configSource; // re-reads the CURRENT value each time it's accessed
        private boolean cachedValue;

        RefreshableFeatureFlagHolder(Supplier<Boolean> configSource) {
            this.configSource = configSource;
            refresh();
        }
        void refresh() { cachedValue = configSource.get(); } // re-reads NOW, on demand
        boolean isEnabled() { return cachedValue; }
    }

    public static void main(String[] args) {
        boolean[] currentConfigValue = {false}; // simulates an external, mutable config source
        RefreshableFeatureFlagHolder holder = new RefreshableFeatureFlagHolder(() -> currentConfigValue[0]);
        System.out.println("Initial: " + holder.isEnabled());

        currentConfigValue[0] = true; // config changes
        System.out.println("Before refresh: " + holder.isEnabled() + " (still stale)");
        holder.refresh(); // explicit refresh trigger -- like /actuator/refresh
        System.out.println("After refresh(): " + holder.isEnabled() + " -- now current!");
    }
}
```

How to run: `java RefreshableHolder.java`

`refresh()` explicitly re-reads `configSource.get()`, updating `cachedValue` to whatever the current configuration now says — this models exactly what happens to a real `@RefreshScope` bean when `/actuator/refresh` is called: the bean is invalidated and its `@Value` bindings are re-evaluated against the current `Environment`.

### Level 3 — Advanced

```java
// File: RefreshScopeRealShape.java -- the REAL Spring Cloud Context
// shape: @RefreshScope makes a bean's @Value bindings re-evaluate on
// every refresh, without any custom refresh() method needed.
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.*;

public class RefreshScopeRealShape {

    @RefreshScope
    @Component
    static class FeatureFlagHolder {
        @Value("${feature.new-checkout.enabled:false}")
        private boolean newCheckoutEnabled;

        boolean isNewCheckoutEnabled() { return newCheckoutEnabled; }
    }

    @RestController
    static class DiagnosticsController {
        private final FeatureFlagHolder featureFlagHolder;
        DiagnosticsController(FeatureFlagHolder featureFlagHolder) { this.featureFlagHolder = featureFlagHolder; }

        @GetMapping("/feature-status")
        public String status() { return "newCheckoutEnabled=" + featureFlagHolder.isNewCheckoutEnabled(); }
    }

    // Operational sequence (as it would run for real):
    // 1. feature.new-checkout.enabled=false -> GET /feature-status returns "false"
    // 2. underlying config source updates to true (e.g. Config Server value changes)
    // 3. POST /actuator/refresh -- Spring recreates the @RefreshScope FeatureFlagHolder proxy
    // 4. GET /feature-status now returns "true" -- with ZERO custom refresh code written
}
```

How to run: requires `spring-boot-starter-actuator`, `spring-cloud-starter-bootstrap` (or the modern `spring-cloud-context` auto-configuration, present transitively via most Spring Cloud starters), and `management.endpoints.web.exposure.include=refresh` set; run via `mvn spring-boot:run`, hit `/feature-status`, update the backing configuration source, call `POST /actuator/refresh`, then hit `/feature-status` again to see the updated value.

`@RefreshScope` handles the re-read automatically — unlike Level 2's hand-written `refresh()` method, `FeatureFlagHolder` here contains no custom refresh logic at all; Spring's `@RefreshScope` proxy machinery is what tears down and recreates the bean (re-evaluating `@Value` against the current `Environment`) whenever a refresh event is received.

## 6. Walkthrough

Trace the operational sequence from Level 3 end to end:

1. **The application starts** with `feature.new-checkout.enabled=false` in its configuration. `FeatureFlagHolder`, being `@RefreshScope`, isn't created as a plain eager singleton — it's represented by a proxy that lazily creates (or reuses) the real underlying instance on first access.
2. **`GET /feature-status` is called.** `DiagnosticsController` calls `featureFlagHolder.isNewCheckoutEnabled()` through the `@RefreshScope` proxy, which creates the real underlying `FeatureFlagHolder` instance (if not already created), binding `newCheckoutEnabled = false` from the current `Environment`. The response is `"newCheckoutEnabled=false"`.
3. **The underlying configuration source is updated** (e.g., a value change in Config Server, or a local property update) to `feature.new-checkout.enabled=true` — at this point, nothing running has changed yet; the already-created `FeatureFlagHolder` instance still holds `false`.
4. **`POST /actuator/refresh` is called.** Spring Cloud Context's refresh mechanism re-reads the `Environment` (picking up the new value) and, critically, invalidates every `@RefreshScope`-managed bean, including `FeatureFlagHolder` — the *proxy* remains the same object other beans hold a reference to, but the real underlying instance behind it is discarded.
5. **`GET /feature-status` is called again.** Because the underlying instance was invalidated in step 4, accessing it through the proxy triggers lazy recreation — a *new* real `FeatureFlagHolder` is constructed, this time binding `newCheckoutEnabled = true` from the now-current `Environment`. The response is `"newCheckoutEnabled=true"`.

The key point: `DiagnosticsController` holds a reference to the same `FeatureFlagHolder` proxy object throughout this entire sequence — it never needed to look up a new bean or be reconstructed itself; the `@RefreshScope` proxy transparently swaps out the real instance underneath it whenever a refresh occurs.

## 7. Gotchas & takeaways

> **Gotcha:** `@RefreshScope` beans are proxies with lazy-recreation semantics, which means they carry a small performance overhead compared to plain singletons (an extra layer of indirection on every method call) — applying it liberally to every bean in an application, rather than specifically to the ones whose configuration genuinely needs to be refreshable at runtime, adds overhead without corresponding benefit.

- Modern Spring Cloud (2020.0+) uses `spring.config.import=optional:configserver:...` instead of a separate bootstrap context — simpler and avoiding an extra context's overhead, while still guaranteeing external configuration loads before the rest of the application depends on it.
- `@RefreshScope` is what makes a bean's `@Value`/`@ConfigurationProperties` bindings re-evaluate against current configuration after a refresh — a plain singleton bean's values are bound once, permanently, at startup.
- `/actuator/refresh` triggers this for one instance; [Spring Cloud Bus's `/actuator/busrefresh`](0537-spring-cloud-bus-for-cross-instance-coordination.md) triggers it fleet-wide from a single call.
- Apply `@RefreshScope` deliberately to beans whose configuration genuinely needs to change at runtime without a restart — not as a default habit on every `@Component`, given its added indirection overhead.
