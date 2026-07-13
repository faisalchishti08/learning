---
card: microservices
gi: 234
slug: refreshscope-for-runtime-refresh
title: "@RefreshScope for runtime refresh"
---

## 1. What it is

`@RefreshScope` is a Spring Cloud annotation that marks a bean as re-creatable at runtime — when a refresh is triggered (via the `/actuator/refresh` endpoint or [Spring Cloud Bus](0235-spring-cloud-bus-config-for-broadcast-refresh.md)), Spring discards the bean's current instance and constructs a fresh one using the latest configuration values, giving ordinary Spring beans the [dynamic runtime configuration refresh](0223-dynamic-runtime-configuration-refresh.md) capability without any manual "live holder" plumbing in application code.

## 2. Why & when

A plain Spring `@Value`-injected field is resolved exactly once, when its containing bean is constructed — updating the underlying configuration source afterward (a [Config Server](0231-spring-cloud-config-server.md) push, an environment change) has no effect on that already-created bean's already-injected value, exactly the "static, frozen at startup" behavior described generally in [dynamic runtime configuration refresh](0223-dynamic-runtime-configuration-refresh.md). `@RefreshScope` closes this gap for ordinary Spring beans without requiring application code to manually implement a live holder pattern — Spring itself handles discarding and recreating the bean when a refresh is triggered, so `@Value`-injected fields on a `@RefreshScope` bean effectively become dynamic.

Apply `@RefreshScope` to beans whose configuration genuinely needs to change without a restart — the same category of settings identified in [dynamic runtime configuration refresh](0223-dynamic-runtime-configuration-refresh.md) as good candidates for dynamic behavior. Beans holding expensive-to-recreate state, or state that other components have taken direct references to and expect to remain stable, are poor candidates, since a refresh discards and replaces the entire bean instance.

## 3. Core concept

`@RefreshScope` wraps the annotated bean in a special scope that, upon receiving a refresh event, invalidates the current instance so the *next* access to it triggers Spring to construct a brand-new instance — re-running the constructor and re-resolving every `@Value` field against the now-current configuration.

```java
@RefreshScope // makes THIS bean discardable-and-recreatable on refresh
@Component
public class RetryConfigBean {
    @Value("${order.retry.max-attempts}")
    int maxAttempts; // re-resolved EVERY time this bean is recreated after a refresh

    int getMaxAttempts() { return maxAttempts; }
}
// POST /actuator/refresh -- triggers Spring to DISCARD the current RetryConfigBean instance;
// the NEXT call to getMaxAttempts() (via a freshly constructed instance) sees the LATEST config value
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A refresh event triggers Spring to discard the current @RefreshScope bean instance; the next access constructs a brand new instance whose @Value fields are re-resolved against the latest configuration" >
  <rect x="20" y="65" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">POST /actuator/refresh</text>

  <rect x="240" y="20" width="170" height="45" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="325" y="47" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Old bean instance DISCARDED</text>

  <rect x="240" y="105" width="170" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="127" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Next access -> NEW instance</text>
  <text x="325" y="140" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">re-resolves @Value fields</text>

  <rect x="470" y="65" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Latest config values</text>

  <line x1="170" y1="87" x2="238" y2="45" stroke="#8b949e" marker-end="url(#arr234)"/>
  <line x1="170" y1="87" x2="238" y2="127" stroke="#8b949e" marker-end="url(#arr234)"/>
  <line x1="410" y1="127" x2="468" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr234g)"/>

  <defs>
    <marker id="arr234" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="arr234g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The refresh event doesn't mutate the bean in place; it discards it, letting the next access build a fresh one from current config.

## 5. Runnable example

Scenario: a retry-config bean modeled first as an ordinary Spring bean whose `@Value`-injected field is frozen after construction (a refresh has no effect on it), refactored to model `@RefreshScope`'s discard-and-recreate behavior explicitly, and finally showing multiple components sharing a `@RefreshScope` bean, all of which see the newly recreated instance's fresh values after a refresh, without any of those components' own code changing.

### Level 1 — Basic

```java
// File: FrozenBeanValue.java -- an ordinary bean's @Value-style field is
// resolved ONCE, at construction; a LATER config change has NO effect.
public class FrozenBeanValue {
    static class RetryConfigBean {
        int maxAttempts;
        RetryConfigBean(int configuredMaxAttempts) { this.maxAttempts = configuredMaxAttempts; } // resolved ONCE
    }

    public static void main(String[] args) {
        int configSource = 3; // simulates "order.retry.max-attempts" in application.yaml
        RetryConfigBean bean = new RetryConfigBean(configSource);
        System.out.println("Bean's maxAttempts: " + bean.maxAttempts);

        configSource = 5; // simulates a config server push -- but the bean was ALREADY constructed
        System.out.println("Config source is now: " + configSource);
        System.out.println("Bean's maxAttempts STILL: " + bean.maxAttempts + " -- frozen at construction, no refresh mechanism.");
    }
}
```

**How to run:** `javac FrozenBeanValue.java && java FrozenBeanValue` (JDK 17+).

### Level 2 — Intermediate

```java
// File: RefreshScopeSimulation.java -- models @RefreshScope's behavior:
// a refresh DISCARDS the current instance; the NEXT access constructs
// a FRESH one from CURRENT config.
import java.util.function.*;

public class RefreshScopeSimulation {
    static class RetryConfigBean {
        int maxAttempts;
        RetryConfigBean(int configuredMaxAttempts) { this.maxAttempts = configuredMaxAttempts; }
    }

    // models the @RefreshScope PROXY: holds NO fixed instance -- constructs one on demand, discards on refresh
    static class RefreshScopeHolder<T> {
        Supplier<T> factory;
        T currentInstance;
        RefreshScopeHolder(Supplier<T> factory) { this.factory = factory; this.currentInstance = factory.get(); }
        T get() { return currentInstance; }
        void refresh() { currentInstance = factory.get(); } // DISCARD and RECREATE, re-running the factory
    }

    static int configSource = 3; // simulates the CURRENT value of "order.retry.max-attempts"

    public static void main(String[] args) {
        RefreshScopeHolder<RetryConfigBean> scopedBean = new RefreshScopeHolder<>(() -> new RetryConfigBean(configSource));
        System.out.println("Before config change: " + scopedBean.get().maxAttempts);

        configSource = 5; // the config source changes (e.g. via a Config Server push)
        System.out.println("Config source updated, but bean not yet refreshed: " + scopedBean.get().maxAttempts); // STILL old, until refresh

        scopedBean.refresh(); // mirrors POST /actuator/refresh
        System.out.println("After refresh(): " + scopedBean.get().maxAttempts); // NEW instance, NEW value
    }
}
```

**How to run:** `javac RefreshScopeSimulation.java && java RefreshScopeSimulation` (JDK 17+).

Expected output:
```
Before config change: 3
Config source updated, but bean not yet refreshed: 3
After refresh(): 5
```

### Level 3 — Advanced

```java
// File: MultipleConsumersShareRefreshedBean.java -- MULTIPLE components
// depend on the SAME @RefreshScope bean; after a refresh, ALL of them
// see the new value through the SAME shared holder, with NO changes
// to any consumer's own code.
import java.util.function.*;
import java.util.*;

public class MultipleConsumersShareRefreshedBean {
    static class RetryConfigBean {
        int maxAttempts;
        RetryConfigBean(int configuredMaxAttempts) { this.maxAttempts = configuredMaxAttempts; }
    }

    static class RefreshScopeHolder<T> {
        Supplier<T> factory;
        T currentInstance;
        RefreshScopeHolder(Supplier<T> factory) { this.factory = factory; this.currentInstance = factory.get(); }
        T get() { return currentInstance; }
        void refresh() { currentInstance = factory.get(); }
    }

    // TWO independent "components," each depending on the SAME RefreshScopeHolder
    static class OrderRetryHandler {
        RefreshScopeHolder<RetryConfigBean> configHolder;
        OrderRetryHandler(RefreshScopeHolder<RetryConfigBean> configHolder) { this.configHolder = configHolder; }
        void describe() { System.out.println("  OrderRetryHandler sees maxAttempts = " + configHolder.get().maxAttempts); }
    }
    static class PaymentRetryHandler {
        RefreshScopeHolder<RetryConfigBean> configHolder;
        PaymentRetryHandler(RefreshScopeHolder<RetryConfigBean> configHolder) { this.configHolder = configHolder; }
        void describe() { System.out.println("  PaymentRetryHandler sees maxAttempts = " + configHolder.get().maxAttempts); }
    }

    static int configSource = 3;

    public static void main(String[] args) {
        RefreshScopeHolder<RetryConfigBean> sharedHolder = new RefreshScopeHolder<>(() -> new RetryConfigBean(configSource));
        OrderRetryHandler orderHandler = new OrderRetryHandler(sharedHolder); // BOTH depend on the SAME holder
        PaymentRetryHandler paymentHandler = new PaymentRetryHandler(sharedHolder);

        System.out.println("Before refresh:");
        orderHandler.describe();
        paymentHandler.describe();

        configSource = 7;
        sharedHolder.refresh(); // ONE refresh call -- affects EVERY consumer holding this SAME holder

        System.out.println("After refresh:");
        orderHandler.describe(); // sees the NEW value -- its own code NEVER changed
        paymentHandler.describe(); // ALSO sees the NEW value -- its own code NEVER changed
    }
}
```

**How to run:** `javac MultipleConsumersShareRefreshedBean.java && java MultipleConsumersShareRefreshedBean` (JDK 17+).

Expected output:
```
Before refresh:
  OrderRetryHandler sees maxAttempts = 3
  PaymentRetryHandler sees maxAttempts = 3
After refresh:
  OrderRetryHandler sees maxAttempts = 7
  PaymentRetryHandler sees maxAttempts = 7
```

## 6. Walkthrough

1. **Level 1, the frozen baseline** — `RetryConfigBean`'s constructor captures `configuredMaxAttempts` into its `maxAttempts` field exactly once; changing `configSource` afterward has no effect on the already-constructed `bean` object, mirroring exactly how a plain (non-`@RefreshScope`) Spring bean's `@Value`-injected field behaves.
2. **Level 2, the discard-and-recreate mechanism** — `RefreshScopeHolder` doesn't hold a value directly; it holds a `factory` (a `Supplier` that knows how to construct a fresh `RetryConfigBean`) and a `currentInstance` produced by that factory, and `refresh()` simply calls `factory.get()` again, replacing `currentInstance` with a brand-new object — this mirrors exactly what Spring's real `@RefreshScope` proxy does internally when a refresh event is received.
3. **Level 2, the gap between config change and bean refresh** — updating `configSource` alone (without calling `refresh()`) has no effect on `scopedBean.get().maxAttempts`, which still returns the old value `3`; this demonstrates that a config source changing and a `@RefreshScope` bean actually refreshing are two distinct events — the refresh has to be explicitly triggered (in a real system, via `/actuator/refresh` or an automated trigger like [Spring Cloud Bus](0235-spring-cloud-bus-config-for-broadcast-refresh.md)).
4. **Level 3, multiple consumers depending on one holder** — `OrderRetryHandler` and `PaymentRetryHandler` each hold a reference to the *same* `sharedHolder` instance, rather than each managing their own separate config resolution — this mirrors how multiple Spring beans injecting the same `@RefreshScope` bean all end up depending on the identical underlying scoped proxy.
5. **Level 3, one refresh call, many consumers affected** — `sharedHolder.refresh()` is called exactly once, yet both `orderHandler.describe()` and `paymentHandler.describe()` report the new value `7` afterward, because both handlers call `configHolder.get()` (which returns whatever `sharedHolder.currentInstance` currently is) rather than caching the bean reference themselves — this is precisely the benefit `@RefreshScope` provides in a real Spring application: a single refresh event propagates to every consumer of the scoped bean simultaneously, without each consuming component needing its own refresh-handling logic.
6. **Level 3, why consumer code never changes** — neither `OrderRetryHandler` nor `PaymentRetryHandler` contains any refresh-specific logic at all; both simply call `configHolder.get().maxAttempts` normally, exactly as they would call a getter on any ordinary object — the refresh mechanics are entirely contained within `RefreshScopeHolder`, which is exactly how `@RefreshScope` lets ordinary application code stay unaware that the beans it depends on are dynamically refreshable.

## 7. Gotchas & takeaways

> **Gotcha:** a component that captures a direct reference to a `@RefreshScope` bean's *contents* (rather than continuing to go through the scoped proxy on every access) can end up holding a stale, pre-refresh value indefinitely — as Level 3 shows, `configHolder.get()` must be called fresh on each use, not once and cached in a local field; Spring's `@RefreshScope` proxy is designed so that normal method calls through the proxy always reach the current instance, but code that manually extracts and stores a value from it early defeats that guarantee.

- `@RefreshScope` lets ordinary Spring beans become dynamically refreshable without application code implementing a manual live-holder pattern itself.
- A refresh discards the bean's current instance and constructs a brand-new one on next access, re-resolving all its `@Value`-injected fields against the latest configuration.
- A configuration source changing and a `@RefreshScope` bean actually being refreshed are distinct events — the refresh must be explicitly triggered, typically via `/actuator/refresh` or [Spring Cloud Bus](0235-spring-cloud-bus-config-for-broadcast-refresh.md) for broadcast refresh across many instances.
- One refresh event correctly propagates to every component depending on the same scoped bean, without any of those components needing their own refresh-specific logic.
- Beans holding expensive-to-recreate state, or state other components have taken direct, cached references to, are poor `@RefreshScope` candidates, since a refresh fully discards and replaces the bean instance.
