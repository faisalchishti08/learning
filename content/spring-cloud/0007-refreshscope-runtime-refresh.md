---
card: spring-cloud
gi: 7
slug: refreshscope-runtime-refresh
title: "@RefreshScope & runtime refresh"
---

## 1. What it is

`@RefreshScope` is the annotation that opts a specific bean into the live-refresh behavior the previous card described conceptually. Spring wraps a `@RefreshScope` bean in a special proxy; when a refresh event fires, the proxy discards its cached target instance, and the next method call transparently triggers lazy re-creation against current configuration.

```java
@RefreshScope
@Component
class RateLimiterConfig {
    @Value("${rate.limit.perMinute}")
    private int limit;

    int getLimit() { return limit; }
}
```

## 2. Why & when

Without `@RefreshScope`, a `@Value`-injected field is read exactly once, when the bean is constructed at application startup, and never again — a classic Spring singleton behavior. `@RefreshScope` is the specific, minimal annotation that changes this for beans that genuinely need to reflect configuration changes at runtime, without making the *entire* application eagerly re-readable (which would be both wasteful and dangerous for stateful beans).

Reach for `@RefreshScope` when:

- A bean's behavior should change when configuration changes, without restarting the application — feature flags, tunable limits, externally configurable endpoints.
- The bean is relatively cheap to recreate — refresh-scoped beans are destroyed and reconstructed on refresh, so heavy initialization logic pays its cost again each time.
- You want the change to apply automatically to every future call, without manually wiring up property-change listeners for each individual configurable value.

## 3. Core concept

```
 @RefreshScope
 @Component
 class RateLimiterConfig {
     @Value("${rate.limit.perMinute}") int limit;
 }

 Spring wraps this in a PROXY, not the real bean directly:

   caller -> RateLimiterConfig$$Proxy -> [cached real instance, OR none yet]
                                              |
                              on refresh: cached instance DISCARDED
                                              |
                    next call -> proxy lazily creates a NEW real instance,
                                  reading @Value against CURRENT Environment
```

The proxy is what makes the bean's identity (from the caller's perspective, an injected `RateLimiterConfig`) stable across refreshes, even though the underlying real instance is periodically swapped out.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Callers hold a reference to a stable proxy, which internally swaps its target instance on refresh">
  <rect x="20" y="65" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">caller</text>

  <line x1="160" y1="85" x2="220" y2="85" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a28)"/>

  <rect x="230" y="65" width="160" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="90" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">stable proxy</text>

  <line x1="390" y1="85" x2="450" y2="85" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a28)"/>

  <rect x="460" y="20" width="160" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="540" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">real instance (before refresh)</text>

  <rect x="460" y="100" width="160" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="125" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">real instance (after refresh)</text>

  <defs><marker id="a28" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The caller's reference to the proxy never changes; the proxy's internal target instance is what gets swapped across a refresh.

## 5. Runnable example

The scenario: a discount-percentage configuration used by an order pricing service, evolving from a plain injected value that never updates, to a `@RefreshScope`-style proxy that transparently swaps its target on refresh, to a demonstration that other, non-refresh-scoped beans holding a *reference* to the refreshed bean still see the update — since they're calling through the same stable proxy.

### Level 1 — Basic

Show the plain-injection baseline: a value read once, permanently fixed.

```java
public class RefreshScopeLevel1 {
    public static void main(String[] args) {
        PricingConfig config = new PricingConfig(readDiscountPercent()); // read ONCE, forever
        System.out.println("Discount: " + config.discountPercent + "%");
        System.out.println("(config source changes, but this instance never notices)");
    }

    static int readDiscountPercent() { return 10; }
}

class PricingConfig {
    final int discountPercent;
    PricingConfig(int discountPercent) { this.discountPercent = discountPercent; }
}
```

How to run: `java RefreshScopeLevel1.java`

`discountPercent` is fixed at construction — the classic singleton behavior `@RefreshScope` exists to opt specific beans out of.

### Level 2 — Intermediate

Add a proxy modeling `@RefreshScope`'s core mechanism: a stable wrapper whose internal target can be discarded and lazily rebuilt.

```java
import java.util.function.*;

public class RefreshScopeLevel2 {
    public static void main(String[] args) {
        ConfigSource source = new ConfigSource(10);

        RefreshScopeProxy<PricingConfig> pricingConfigProxy =
            new RefreshScopeProxy<>(() -> new PricingConfig(source.discountPercent));

        System.out.println("Before change: " + pricingConfigProxy.get().discountPercent + "%");

        source.discountPercent = 25; // config changes at the source
        System.out.println("After change, before refresh: " + pricingConfigProxy.get().discountPercent + "%"); // still old

        pricingConfigProxy.refresh(); // simulates a refresh event reaching this bean
        System.out.println("After refresh: " + pricingConfigProxy.get().discountPercent + "%"); // now current
    }
}

class ConfigSource { int discountPercent; ConfigSource(int discountPercent) { this.discountPercent = discountPercent; } }
class PricingConfig { final int discountPercent; PricingConfig(int discountPercent) { this.discountPercent = discountPercent; } }

// Stands in for the @RefreshScope proxy: stable identity, swappable target.
class RefreshScopeProxy<T> {
    private final Supplier<T> factory;
    private T target;
    RefreshScopeProxy(Supplier<T> factory) { this.factory = factory; this.target = factory.get(); }
    T get() { return target; }
    void refresh() { target = factory.get(); } // discard cached target, lazily recreate on next construction
}
```

How to run: `java RefreshScopeLevel2.java`

`pricingConfigProxy` itself is never replaced — only its internal `target` is, on `refresh()` — mirroring how injecting a `@RefreshScope` bean gives callers a reference to the *proxy*, which stays valid and stable across any number of underlying refreshes.

### Level 3 — Advanced

Show that a *different* bean holding a reference to the refresh-scoped proxy also sees the update automatically — because it's holding the same stable proxy reference, not a copy of a value.

```java
import java.util.function.*;

public class RefreshScopeLevel3 {
    public static void main(String[] args) {
        ConfigSource source = new ConfigSource(10);
        RefreshScopeProxy<PricingConfig> pricingConfigProxy =
            new RefreshScopeProxy<>(() -> new PricingConfig(source.discountPercent));

        // A SEPARATE service holds a reference to the SAME proxy -- injected once, just like real Spring DI.
        OrderPricingService pricingService = new OrderPricingService(pricingConfigProxy);

        System.out.println("Order total before refresh: $" + pricingService.priceOrder(100.0));

        source.discountPercent = 25;
        pricingConfigProxy.refresh(); // ONE refresh call...

        // ...and the service, which was never touched or reconfigured, sees the NEW discount automatically.
        System.out.println("Order total after refresh:  $" + pricingService.priceOrder(100.0));
    }
}

class ConfigSource { int discountPercent; ConfigSource(int discountPercent) { this.discountPercent = discountPercent; } }
class PricingConfig { final int discountPercent; PricingConfig(int discountPercent) { this.discountPercent = discountPercent; } }

class RefreshScopeProxy<T> {
    private final Supplier<T> factory;
    private T target;
    RefreshScopeProxy(Supplier<T> factory) { this.factory = factory; this.target = factory.get(); }
    T get() { return target; }
    void refresh() { target = factory.get(); }
}

// This service was constructed ONCE, injected with the proxy, and never reconfigured -- yet it stays current.
class OrderPricingService {
    private final RefreshScopeProxy<PricingConfig> pricingConfigProxy;
    OrderPricingService(RefreshScopeProxy<PricingConfig> pricingConfigProxy) { this.pricingConfigProxy = pricingConfigProxy; }

    double priceOrder(double baseAmount) {
        int discount = pricingConfigProxy.get().discountPercent; // reads through the proxy on EVERY call
        return baseAmount * (100 - discount) / 100.0;
    }
}
```

How to run: `java RefreshScopeLevel3.java`

`OrderPricingService` is constructed exactly once and never touched again after that — no refresh logic of its own — yet `priceOrder` reflects the updated discount immediately after `pricingConfigProxy.refresh()`, because it calls `pricingConfigProxy.get()` fresh on every invocation, and the proxy's `get()` always returns whatever the current target happens to be.

## 6. Walkthrough

Execution starts in `main` for Level 3. `pricingConfigProxy` is constructed with a `discountPercent` of `10`, and `pricingService` is constructed holding a reference to that same proxy object — not a copy of its current value, but the proxy itself.

`pricingService.priceOrder(100.0)` calls `pricingConfigProxy.get().discountPercent`, getting `10`, and computes `100.0 * (100 - 10) / 100.0`:

```
Order total before refresh: $90.0
```

`source.discountPercent = 25` changes the underlying config value, and `pricingConfigProxy.refresh()` discards the cached `PricingConfig` target and lazily constructs a new one reading the now-current `source.discountPercent = 25`. `pricingService` itself is never called or modified during this step.

The second `priceOrder(100.0)` call again calls `pricingConfigProxy.get()` — this time returning the *new* target instance with `discountPercent = 25`:

```
Order total after refresh:  $75.0
```

In a real Spring Cloud application, this is exactly the payoff of `@RefreshScope`: any number of other beans can hold an injected reference to a refresh-scoped bean, and all of them transparently see updated configuration after a single refresh event, without any of those dependent beans needing their own refresh-awareness — they're simply calling methods on a proxy whose internal target happens to have been swapped.

## 7. Gotchas & takeaways

> Gotcha: `@RefreshScope` beans are proxied using CGLIB by default, which requires the bean's class to be non-`final` and have a default constructor (or otherwise be proxyable) — a `final` class or one relying only on constructor injection with no accessible no-arg constructor can fail to be wrapped correctly, surfacing as a confusing proxying error at startup rather than at refresh time.

> Gotcha: holding a *copy* of a value read from a `@RefreshScope` bean (e.g. assigning `int cachedDiscount = pricingConfig.getDiscountPercent();` once and reusing that local variable) breaks the refresh behavior entirely — only calls that go *through* the proxy on each use see updates; a value copied out and held separately is just as stale as if refresh scope weren't used at all.

- `@RefreshScope` wraps a bean in a proxy with a stable identity but a swappable internal target, letting the bean's configuration update live without restarting the application.
- Other beans holding a reference to a refresh-scoped bean automatically see its updates too, as long as they read through the proxy on each use rather than caching a copied-out value.
- Refresh-scoped beans pay their full initialization cost again on every refresh — reserve the annotation for beans where that's an acceptable trade-off for runtime configurability.
- The proxying mechanism has real constraints (non-final classes, proxyable construction) worth knowing before reaching for `@RefreshScope` on an arbitrary bean.
