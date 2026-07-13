---
card: microservices
gi: 443
slug: externalized-config-stateless-processes
title: "Externalized config & stateless processes"
---

## 1. What it is

**Externalized configuration** means everything that varies between environments — database URLs, API keys, feature flags, timeouts — lives outside the compiled application artifact, supplied at startup (or runtime) via environment variables, mounted config files, or a config server, rather than hardcoded or baked into the build. **Stateless processes** means an application instance keeps no data in memory or on local disk that must survive beyond a single request, or that other instances would need to know about — anything that must persist gets written to a shared backing service (a database, a cache, an external session store) instead. These are factors 3 and 6 of the [twelve-factor app principles](0442-twelve-factor-app-principles.md), pulled out here because together they're what actually makes "the same image runs identically everywhere and any instance can serve any request" true in practice, not just in principle.

## 2. Why & when

These two disciplines matter because they're direct prerequisites for the operational properties containerized microservices rely on:

- **One build, many environments.** With config externalized, the exact same image (built once, per [container image building](0438-container-image-building.md)) runs correctly in dev, staging, and production — only its environment differs. Without this, you'd need environment-specific builds, breaking [immutable infrastructure](0437-immutable-infrastructure.md)'s promise of a single, verified artifact.
- **Safe horizontal scaling and load balancing.** A load balancer routing requests to a fleet needs to be able to send any request to any instance. If an instance keeps state locally (an in-memory session cache, a file written to local disk), routing the next related request to a different instance silently breaks — the classic symptom is "it works until we scale past one instance" or "logging in works but my session randomly gets lost."
- **Safe restarts and replacements.** An orchestrator that kills and replaces an unhealthy instance assumes nothing important is lost by doing so — true only if the instance held no state the rest of the system depended on. A stateful instance turns every restart into a potential data-loss event.
- **Secrets shouldn't live in source control.** Baking a database password or API key into application code or a config file checked into Git means it's in your version history forever, visible to anyone with repo access, and hard to rotate — externalizing secrets (often via a dedicated secrets manager) avoids this entirely.

You apply these disciplines to every service from day one — retrofitting statelessness onto a service that's already accumulated local session caches, local file writes, or in-memory queues is a much harder, riskier migration than designing for it from the start.

## 3. Core concept

Think of externalized configuration and statelessness like a hotel's approach to guest belongings versus a private, permanently-owned apartment. In a hotel room (a stateless process), nothing that matters long-term is stored *in* the room itself — your reservation, your loyalty points, your billing details all live in the hotel's central system (a backing service), so you could check into a *different* room tomorrow and the hotel still knows exactly who you are. If you left something valuable hidden under the mattress (state kept only in local instance memory or disk), it's gone the moment housekeeping resets that specific room for the next guest — which is exactly what happens when an orchestrator terminates and replaces a container.

Concretely, the two disciplines work through:

1. **Config sourced from the environment at startup**, not hardcoded — in Spring Boot, this means `application.yml` properties are overridable by environment variables (`${DATABASE_URL}`) or Kubernetes-injected `ConfigMap`/`Secret` values, following a well-defined precedence order (command-line args > environment variables > config files > defaults).
2. **Secrets handled distinctly from ordinary config** — often injected via a dedicated secrets manager or mounted secret volume rather than a plain environment variable, specifically because environment variables can leak more easily (process listings, crash dumps, child process inheritance) than a properly access-controlled secret store.
3. **Anything that must outlive a single request goes to a backing service** — a session goes to Redis or a database, not an in-memory `HashMap`; a file upload goes to object storage, not local disk; a background job's progress goes to a database row, not a static field.
4. **The process itself carries no identity that matters** — instance `order-service-7` and instance `order-service-12` should be functionally interchangeable at all times; if killing one and starting a fresh one changes user-visible behavior, some state has leaked into the process that shouldn't be there.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stateless process reads configuration from the environment at startup and stores no durable state locally; anything that must persist is written to an external backing service shared by every instance, so any instance can be freely replaced" >
  <rect x="30" y="20" width="580" height="20" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="34" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Environment: DATABASE_URL, API_KEY, FEATURE_FLAG_X (injected at startup)</text>

  <rect x="60" y="60" width="130" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="125" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance-1</text>
  <text x="125" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">config from env</text>
  <text x="125" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no local state</text>

  <rect x="230" y="60" width="130" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="295" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance-2</text>
  <text x="295" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">config from env</text>
  <text x="295" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no local state</text>

  <rect x="400" y="60" width="130" height="70" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="2" stroke-dasharray="4,2"/>
  <text x="465" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance-3</text>
  <text x="465" y="98" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">killed &amp; replaced</text>
  <text x="465" y="112" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">nothing is lost</text>

  <line x1="125" y1="130" x2="320" y2="170" stroke="#79c0ff"/>
  <line x1="295" y1="130" x2="320" y2="170" stroke="#79c0ff"/>
  <line x1="465" y1="130" x2="320" y2="170" stroke="#79c0ff" stroke-dasharray="3,2"/>

  <rect x="250" y="170" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="320" y="192" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">shared backing service</text>
  <text x="320" y="207" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">DB / cache / session store</text>

  <text x="320" y="240" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">any instance can be freely killed and replaced without losing anything durable</text>
</svg>

Configuration flows in from the environment at startup; anything durable flows out to a shared backing service, leaving the process itself freely replaceable.

## 5. Runnable example

Scenario: an `order-service` reading its configuration and handling in-flight orders. We model config precedence (environment overriding defaults) first, then externalize a stateful in-memory cart into a shared store, then handle a production-flavored case: a config reload that must apply safely across a running fleet without any instance restarting with stale or half-applied values.

### Level 1 — Basic

```java
// File: ConfigPrecedenceBasic.java -- models the CORE idea: configuration
// resolves from multiple sources with a defined PRECEDENCE, environment
// variables overriding defaults, exactly as Spring Boot's property
// resolution does.
import java.util.*;

public class ConfigPrecedenceBasic {
    static class Config {
        final Map<String, String> defaults;
        final Map<String, String> environment;

        Config(Map<String, String> defaults, Map<String, String> environment) {
            this.defaults = defaults;
            this.environment = environment;
        }

        String get(String key) {
            // Environment always wins over the compiled-in default.
            return environment.getOrDefault(key, defaults.get(key));
        }
    }

    public static void main(String[] args) {
        Map<String, String> defaults = Map.of(
                "database.url", "jdbc:postgresql://localhost:5432/orders_dev",
                "timeout.ms", "3000");

        Map<String, String> prodEnvironment = Map.of(
                "database.url", "jdbc:postgresql://prod-db.internal:5432/orders");
        // Note: prod does NOT override timeout.ms -- it falls back to the default.

        Config config = new Config(defaults, prodEnvironment);

        System.out.println("database.url = " + config.get("database.url") + " (overridden by environment)");
        System.out.println("timeout.ms   = " + config.get("timeout.ms") + " (falls back to default -- environment didn't specify it)");
    }
}
```

How to run: `java ConfigPrecedenceBasic.java`

`Config.get` checks `environment` first and only falls back to `defaults` if the environment doesn't specify a key — the same precedence Spring Boot applies when an environment variable like `DATABASE_URL` overrides a value declared in `application.yml`. `database.url` resolves to the production value because the environment supplies it; `timeout.ms` resolves to the compiled-in default because the environment doesn't mention it — both behaviors are correct and expected, not a bug.

### Level 2 — Intermediate

```java
// File: ExternalizedCartStoreIntermediate.java -- the SAME service, now
// moving a shopping cart from LOCAL, per-instance memory to a SHARED
// backing service, so any instance can serve any request for it.
import java.util.*;

public class ExternalizedCartStoreIntermediate {
    // A stand-in for a real shared store (Redis, a database table) -- the
    // key property is that EVERY instance reads and writes the SAME store.
    static class SharedCartStore {
        private final Map<String, List<String>> carts = new HashMap<>();
        void addItem(String cartId, String item) {
            carts.computeIfAbsent(cartId, k -> new ArrayList<>()).add(item);
        }
        List<String> getItems(String cartId) {
            return carts.getOrDefault(cartId, List.of());
        }
    }

    static class OrderServiceInstance {
        final String instanceId;
        final SharedCartStore store;

        OrderServiceInstance(String instanceId, SharedCartStore store) {
            this.instanceId = instanceId;
            this.store = store;
        }

        void addToCart(String cartId, String item) {
            store.addItem(cartId, item);
            System.out.println("[" + instanceId + "] added '" + item + "' to cart " + cartId);
        }

        void checkout(String cartId) {
            List<String> items = store.getItems(cartId);
            System.out.println("[" + instanceId + "] checking out cart " + cartId + " with items: " + items);
        }
    }

    public static void main(String[] args) {
        SharedCartStore shared = new SharedCartStore();
        OrderServiceInstance addHandler = new OrderServiceInstance("instance-1", shared);
        OrderServiceInstance checkoutHandler = new OrderServiceInstance("instance-2", shared);

        addHandler.addToCart("cart-77", "widget");
        addHandler.addToCart("cart-77", "gadget");

        // A DIFFERENT instance handles checkout -- it still sees the full cart.
        checkoutHandler.checkout("cart-77");
    }
}
```

How to run: `java ExternalizedCartStoreIntermediate.java`

`SharedCartStore` is deliberately a single object referenced by both `OrderServiceInstance`s, standing in for a real external store both instances would connect to over the network. `addHandler` (`instance-1`) adds two items; `checkoutHandler` (`instance-2`), a completely different instance, is still able to see the full cart at checkout — because the cart was never tied to either instance's local memory in the first place, this works correctly regardless of which instance handles which request.

### Level 3 — Advanced

```java
// File: SafeConfigReloadAdvanced.java -- the SAME externalized-config idea,
// now handling a PRODUCTION-FLAVORED hard case: a config value changes at
// runtime (e.g. via Spring Cloud Bus / Actuator refresh), and the reload
// must be applied ATOMICALLY per instance -- never leaving a request
// straddling old and new config values mid-flight.
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;

public class SafeConfigReloadAdvanced {
    record ServiceConfig(String databaseUrl, int timeoutMs, boolean newCheckoutFlowEnabled) {}

    static class ReloadableConfigHolder {
        // AtomicReference gives every in-flight request a CONSISTENT snapshot:
        // a reload swaps the whole object at once, never mutates fields individually.
        private final AtomicReference<ServiceConfig> current;

        ReloadableConfigHolder(ServiceConfig initial) { this.current = new AtomicReference<>(initial); }

        ServiceConfig snapshot() { return current.get(); }

        void reload(ServiceConfig updated) {
            ServiceConfig previous = current.getAndSet(updated);
            System.out.println("Config reloaded: newCheckoutFlowEnabled " + previous.newCheckoutFlowEnabled()
                    + " -> " + updated.newCheckoutFlowEnabled());
        }
    }

    static void handleRequest(String requestId, ReloadableConfigHolder holder) {
        // Each request takes ONE consistent snapshot at the start -- even if
        // reload() runs concurrently, THIS request's view never changes mid-flight.
        ServiceConfig configForThisRequest = holder.snapshot();
        System.out.println("[" + requestId + "] using timeout=" + configForThisRequest.timeoutMs()
                + "ms, newCheckoutFlowEnabled=" + configForThisRequest.newCheckoutFlowEnabled());
    }

    public static void main(String[] args) {
        ServiceConfig v1 = new ServiceConfig("jdbc:postgresql://prod-db.internal:5432/orders", 3000, false);
        ReloadableConfigHolder holder = new ReloadableConfigHolder(v1);

        handleRequest("req-1", holder); // sees v1, old checkout flow

        // Ops flips a feature flag via a config refresh -- the running
        // instance is NOT restarted; it just picks up new values.
        ServiceConfig v2 = new ServiceConfig(v1.databaseUrl(), v1.timeoutMs(), true);
        holder.reload(v2);

        handleRequest("req-2", holder); // sees v2, new checkout flow enabled

        boolean req1SawStableConfig = true; // by construction: it took ONE snapshot, never re-read mid-handling
        System.out.println("req-1's config view was internally consistent throughout its handling: " + req1SawStableConfig);
    }
}
```

How to run: `java SafeConfigReloadAdvanced.java`

The hard case is a *live* config reload — something [twelve-factor app principles](0442-twelve-factor-app-principles.md) explicitly wants to be possible without a restart, but which is dangerous if done carelessly: a request that reads part of its config before a reload and part after could end up in an inconsistent, half-old-half-new state. `AtomicReference<ServiceConfig>` ensures `reload` swaps the *entire* config object atomically, and `handleRequest` takes exactly one `snapshot()` at the start of handling — so no single request can ever observe a config value change mid-flight, even though the holder's overall config does change over time as later requests arrive.

## 6. Walkthrough

Trace `SafeConfigReloadAdvanced.main` in order. **First**, `v1` is created with `newCheckoutFlowEnabled = false`, and `holder` wraps it in an `AtomicReference`. `handleRequest("req-1", holder)` calls `holder.snapshot()`, which returns `v1` — this snapshot is a plain, immutable `ServiceConfig` value, not a live view into `holder`, so nothing that happens to `holder` afterward can retroactively change what `req-1` already read.

**Next**, `v2` is built from `v1`'s existing `databaseUrl` and `timeoutMs`, but with `newCheckoutFlowEnabled` flipped to `true` — modeling an operator toggling a feature flag through a runtime config refresh mechanism, without restarting the process. `holder.reload(v2)` calls `current.getAndSet(v2)`, which atomically replaces the entire config object in one operation and returns the previous value (`v1`) for logging.

**Then**, `handleRequest("req-2", holder)` calls `holder.snapshot()` again, this time getting `v2` — the new flag value. Because each request calls `snapshot()` exactly once at the start of its own handling, `req-1` (which ran entirely before the reload) and `req-2` (which ran entirely after) each see one single, internally consistent config value for their whole duration — neither straddles the transition.

**Finally**, `req1SawStableConfig` is asserted `true` by construction: since `req-1`'s handling took its one snapshot before `reload` was ever called, and `ServiceConfig` is an immutable record whose fields can't change after construction, there's no code path by which `req-1` could have observed a partially updated config.

```
[req-1] using timeout=3000ms, newCheckoutFlowEnabled=false
Config reloaded: newCheckoutFlowEnabled false -> true
[req-2] using timeout=3000ms, newCheckoutFlowEnabled=true
req-1's config view was internally consistent throughout its handling: true
```

## 7. Gotchas & takeaways

> Environment variables are a convenient way to inject configuration, but they are not automatically a secure way to inject secrets — they can appear in process listings (`ps aux`), crash dumps, and are inherited by every child process a service spawns. For genuine secrets (database passwords, API keys, signing keys), prefer a dedicated secrets manager or mounted secret volume with tighter access control, rather than treating them identically to ordinary, non-sensitive configuration values.

- Config precedence (environment overriding file-based defaults) is what lets one built artifact run correctly, unmodified, in every environment — verify this precedence explicitly rather than assuming it, since a misconfigured override order can silently ignore a production value in favor of a hardcoded default.
- Anything that must survive beyond a single request — sessions, carts, in-progress workflow state — belongs in a shared backing service, never in an instance's local memory or local disk, or horizontal scaling and load balancing silently break.
- Live config reloads are genuinely useful (feature flags, log levels) but must be applied atomically per in-flight request, or you risk a single request observing an inconsistent mix of old and new values partway through its own handling.
- These two disciplines directly implement factors 3 and 6 of the [twelve-factor app principles](0442-twelve-factor-app-principles.md) — see that entry for how they fit alongside disposability, dev/prod parity, and the other ten factors.
- Spring Boot's property resolution (`application.yml` overridable by environment variables and `@RefreshScope`-aware beans for live reload) implements most of this mechanism directly, so reach for those built-in features before hand-rolling a config precedence or reload system.
