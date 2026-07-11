---
card: spring-cloud
gi: 118
slug: reloading-config-on-change
title: "Reloading config on change"
---

## 1. What it is

Spring Cloud Kubernetes can watch ConfigMaps and Secrets for changes (via the Kubernetes API's watch mechanism, or by periodically polling) and automatically trigger a configuration refresh — either restarting the application context (`spring.cloud.kubernetes.reload.strategy=restart_context`) or refreshing only `@RefreshScope` beans (`refresh`, matching the `/actuator/refresh` mechanism from earlier Config Server cards) — the moment a ConfigMap or Secret an application depends on is updated, with no manual `/actuator/refresh` call or Spring Cloud Bus broadcast needed.

```properties
spring.cloud.kubernetes.reload.enabled=true
spring.cloud.kubernetes.reload.strategy=refresh
spring.cloud.kubernetes.reload.mode=event
```

```java
@RefreshScope
@Component
class RateLimitConfig {
    @Value("${rate-limit}")
    String rateLimit; // automatically re-bound when the backing ConfigMap changes, no manual trigger needed
}
```

## 2. Why & when

Earlier cards established `/actuator/busrefresh` as the mechanism for broadcasting a configuration reload across a fleet on demand, triggered by an operator or a Git webhook — but that still requires *something* to notice a configuration change happened and issue the trigger. Spring Cloud Kubernetes's reload feature closes this final gap specifically for Kubernetes-native configuration: because Kubernetes' own API server already provides a watch mechanism that notifies subscribers the instant a ConfigMap or Secret's contents change, Spring Cloud Kubernetes can subscribe to that watch directly and initiate the refresh itself, with zero external trigger, webhook, or bus broadcast required — updating a ConfigMap's data with `kubectl apply` is, by itself, sufficient to propagate that change into every subscribed application's running configuration.

Reach for config reload on change when:

- Configuration lives in Kubernetes ConfigMaps/Secrets (from the earlier `PropertySource` card) and should take effect automatically the moment it's updated, without a separate manual refresh trigger or redeploy.
- `refresh` mode (re-binding `@RefreshScope` beans) is sufficient for the kind of configuration changing — this is generally preferable to `restart_context` mode, since it avoids the disruption of a full application context restart for what might be a small property change.
- `restart_context` mode is specifically needed because the changed configuration affects beans or wiring that `@RefreshScope`'s narrower rebinding can't reach — a heavier-handed but more thorough reload, appropriate when configuration changes require re-initializing more of the application than `@RefreshScope` alone covers.

## 3. Core concept

```
 operator runs: kubectl apply -f updated-configmap.yaml
        |
        v
 Kubernetes API server updates the ConfigMap object, notifies WATCHERS
        |
        v
 Spring Cloud Kubernetes's watch subscription receives the change notification
        |
        v
 reload triggered automatically:
   mode=refresh          -> only @RefreshScope beans rebind (lighter-weight)
   mode=restart_context   -> the WHOLE application context restarts (heavier, but more thorough)

 NO operator action beyond the original kubectl apply -- NO /actuator/busrefresh call needed
```

The watch-driven trigger is what distinguishes this from the Config-Server-plus-Bus approach covered in earlier cards — there, an external event (a webhook, a manual call) initiates the broadcast; here, the platform's own change notification does.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An operator applies an updated ConfigMap which the Kubernetes API server propagates as a watch notification directly to the application triggering an automatic refresh scope rebind with no separate manual trigger step">
  <rect x="20" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="48" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">kubectl apply</text>

  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Kubernetes API server</text>
  <text x="320" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">notifies watchers</text>

  <rect x="480" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">application</text>
  <text x="550" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">auto-refreshes</text>

  <defs><marker id="a118" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="160" y1="43" x2="230" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a118)"/>
  <line x1="410" y1="43" x2="480" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a118)"/>
</svg>

Three steps, zero manual "trigger the refresh" action from the operator beyond the original config change itself.

## 5. Runnable example

The scenario: model a watch-driven ConfigMap change notification triggering an automatic rebind of `@RefreshScope`-style beans, contrasted against a plain (non-reloading) bean that keeps its stale value. Start with a bean requiring manual refresh (the baseline problem), then add watch-driven automatic refresh, then add `restart_context`-style full reinitialization for a case where lighter refresh isn't sufficient.

### Level 1 — Basic

A plain, non-reloading configuration bean — its value is fixed at construction and never changes, even if the underlying source is updated.

```java
import java.util.*;

public class ReloadConfigLevel1 {
    static Map<String, String> configMapData = new HashMap<>(Map.of("rate-limit", "100/min"));

    static class RateLimitConfig {
        String rateLimit;
        RateLimitConfig() { this.rateLimit = configMapData.get("rate-limit"); } // bound ONCE, at construction
    }

    public static void main(String[] args) {
        RateLimitConfig config = new RateLimitConfig();
        System.out.println("initial rate limit: " + config.rateLimit);

        configMapData.put("rate-limit", "50/min"); // ConfigMap updated -- but the bean was NEVER told
        System.out.println("after ConfigMap update, bean STILL reports: " + config.rateLimit + " (STALE)");
    }
}
```

How to run: `java ReloadConfigLevel1.java`

Even though `configMapData` was updated to `"50/min"`, `config.rateLimit` still reports the original `"100/min"`, because it was read once at construction and never re-read — this staleness is exactly what automatic reload eliminates.

### Level 2 — Intermediate

Add a watch mechanism: a listener subscribed to ConfigMap changes automatically triggers a rebind, mirroring `@RefreshScope`'s behavior under `mode=refresh`.

```java
import java.util.*;
import java.util.function.Consumer;

public class ReloadConfigLevel2 {
    static class ConfigMapWatcher {
        Map<String, String> data;
        List<Consumer<Map<String, String>>> listeners = new ArrayList<>();
        ConfigMapWatcher(Map<String, String> initialData) { this.data = new HashMap<>(initialData); }

        void subscribe(Consumer<Map<String, String>> listener) { listeners.add(listener); }

        void applyUpdate(Map<String, String> newData) {
            data = new HashMap<>(newData);
            System.out.println("ConfigMap updated -- notifying " + listeners.size() + " watcher(s)");
            for (Consumer<Map<String, String>> listener : listeners) listener.accept(data); // automatic notification
        }
    }

    static class RateLimitConfig {
        String rateLimit;
        void rebind(Map<String, String> newData) {
            rateLimit = newData.get("rate-limit");
            System.out.println("RateLimitConfig REBOUND: rateLimit=" + rateLimit);
        }
    }

    public static void main(String[] args) {
        ConfigMapWatcher watcher = new ConfigMapWatcher(Map.of("rate-limit", "100/min"));
        RateLimitConfig config = new RateLimitConfig();
        config.rebind(watcher.data); // initial bind

        watcher.subscribe(config::rebind); // registers for FUTURE automatic updates

        System.out.println("-- operator runs kubectl apply with an updated ConfigMap --");
        watcher.applyUpdate(Map.of("rate-limit", "50/min")); // triggers automatic rebind, no manual call needed

        System.out.println("final rateLimit: " + config.rateLimit);
    }
}
```

How to run: `java ReloadConfigLevel2.java`

`watcher.applyUpdate` is the only call the "operator" makes — `config.rebind` runs automatically as a direct consequence, because it was registered as a listener via `watcher.subscribe(config::rebind)`, exactly mirroring how Spring Cloud Kubernetes's watch on a real ConfigMap automatically triggers `@RefreshScope` bean rebinding with no separate refresh call needed from the operator.

### Level 3 — Advanced

Add `restart_context`-style handling: a configuration change that a lighter `refresh` can't fully address (say, a change affecting bean wiring itself, not just a property value) triggers a full context "restart" — modeled as tearing down and rebuilding every registered component.

```java
import java.util.*;
import java.util.function.Consumer;

public class ReloadConfigLevel3 {
    static class ConfigMapWatcher {
        Map<String, String> data;
        List<Consumer<Map<String, String>>> refreshListeners = new ArrayList<>();
        Runnable restartContextHandler;
        ConfigMapWatcher(Map<String, String> initialData) { this.data = new HashMap<>(initialData); }

        void subscribeRefresh(Consumer<Map<String, String>> listener) { refreshListeners.add(listener); }
        void onRestartRequired(Runnable handler) { restartContextHandler = handler; }

        void applyUpdate(Map<String, String> newData, boolean requiresFullRestart) {
            data = new HashMap<>(newData);
            if (requiresFullRestart) {
                System.out.println("change requires FULL context restart (mode=restart_context)");
                restartContextHandler.run();
            } else {
                System.out.println("change is refresh-scope-safe (mode=refresh)");
                for (Consumer<Map<String, String>> listener : refreshListeners) listener.accept(data);
            }
        }
    }

    static class ApplicationContext {
        String rateLimit;
        boolean fullyReinitialized = false;

        void rebindRefreshScope(Map<String, String> newData) { rateLimit = newData.get("rate-limit"); }

        void restartFully(Map<String, String> newData) {
            System.out.println("tearing down and rebuilding the ENTIRE application context...");
            rateLimit = newData.get("rate-limit");
            fullyReinitialized = true;
        }
    }

    public static void main(String[] args) {
        ConfigMapWatcher watcher = new ConfigMapWatcher(Map.of("rate-limit", "100/min", "connection-pool.strategy", "fixed"));
        ApplicationContext ctx = new ApplicationContext();
        ctx.rebindRefreshScope(watcher.data);

        watcher.subscribeRefresh(ctx::rebindRefreshScope);
        watcher.onRestartRequired(() -> ctx.restartFully(watcher.data));

        System.out.println("-- simple rate-limit change (refresh-safe) --");
        watcher.applyUpdate(Map.of("rate-limit", "50/min", "connection-pool.strategy", "fixed"), false);
        System.out.println("rateLimit=" + ctx.rateLimit + ", fully reinitialized? " + ctx.fullyReinitialized);

        System.out.println("-- connection-pool STRATEGY change (needs restart_context) --");
        watcher.applyUpdate(Map.of("rate-limit", "50/min", "connection-pool.strategy", "elastic"), true);
        System.out.println("rateLimit=" + ctx.rateLimit + ", fully reinitialized? " + ctx.fullyReinitialized);
    }
}
```

How to run: `java ReloadConfigLevel3.java`

The first update (`requiresFullRestart=false`) triggers only `ctx.rebindRefreshScope`, leaving `ctx.fullyReinitialized` at `false`; the second update (`requiresFullRestart=true`) instead triggers `ctx.restartFully`, which sets `fullyReinitialized` to `true` — modeling how a configuration change affecting something beyond simple `@RefreshScope`-bound values (bean wiring, connection pool implementation strategy) genuinely needs the heavier `restart_context` mode to take full effect correctly, rather than the lighter `refresh` mode alone.

## 6. Walkthrough

Trace the second `applyUpdate` call (`requiresFullRestart=true`) in Level 3.

1. `watcher.applyUpdate(Map.of(...), true)` is called — `data` is updated to the new map, and because `requiresFullRestart` is `true`, the `if` branch runs instead of the `else`.
2. `println` reports the full-restart requirement, then `restartContextHandler.run()` executes — this was registered earlier as `() -> ctx.restartFully(watcher.data)`, a lambda capturing `ctx` and a reference to `watcher.data` (evaluated at call time, so it reads the already-updated data).
3. Inside `ctx.restartFully(newData)`, `println` reports the teardown/rebuild happening, `rateLimit` is set to `newData.get("rate-limit")` (`"50/min"`, unchanged from the previous update since only `connection-pool.strategy` changed this time), and `fullyReinitialized` is set to `true`.
4. Note that `refreshListeners` (which would include `ctx::rebindRefreshScope`) was never invoked on this path — the `if`/`else` branching means exactly one of the two reload strategies runs per update, never both, mirroring how a real Spring Cloud Kubernetes deployment is configured with one `reload.strategy` value, not a per-change choice between the two.
5. The final `println` confirms `rateLimit=50/min` (correct, carried through via `restartFully`'s own explicit rebinding) and `fullyReinitialized=true`, correctly reflecting that this particular update took the heavier path.

```
applyUpdate(newData, requiresFullRestart=true):
  if true  -> restartContextHandler.run() -> ctx.restartFully(newData)
                -> rateLimit rebound, fullyReinitialized = true
  (refreshListeners NEVER called on this path)

applyUpdate(newData, requiresFullRestart=false):
  else -> refreshListeners each notified -> ctx.rebindRefreshScope(newData)
                -> rateLimit rebound, fullyReinitialized UNCHANGED (stays false)
```

## 7. Gotchas & takeaways

> **Gotcha:** `restart_context` mode restarts the *entire* Spring application context, which briefly makes the application unavailable to serve requests during that restart — using it as the default reload strategy for every configuration change, rather than reserving it specifically for changes `@RefreshScope`'s lighter rebinding genuinely can't handle, introduces avoidable downtime on every routine configuration update. Default to `refresh` mode unless a specific, identified need for full context restart exists.

- Watch-driven reload eliminates the need for a separate manual trigger (an `/actuator/busrefresh` call, a webhook) specifically for Kubernetes-native ConfigMap/Secret changes — the platform's own change notification is the trigger.
- `refresh` mode (rebinding `@RefreshScope` beans) is the lighter-weight, generally preferable option for configuration changes that are simple property value updates; `restart_context` mode is reserved for changes that affect deeper wiring `@RefreshScope` alone can't reach.
- This reload mechanism builds directly on the ConfigMap/Secrets `PropertySource` from the earlier card — reload is specifically about *when* a refresh happens (automatically, on watched change) rather than changing how configuration values are read into the application in the first place.
- Testing reload behavior deliberately (updating a ConfigMap in a test or staging environment and confirming the expected refresh or restart actually occurs) is worth doing explicitly before relying on it in production, since the practical behavior depends on correctly configured RBAC permissions for the application to watch ConfigMaps/Secrets via the Kubernetes API in the first place.
