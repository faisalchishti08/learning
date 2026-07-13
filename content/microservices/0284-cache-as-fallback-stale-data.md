---
card: microservices
gi: 284
slug: cache-as-fallback-stale-data
title: "Cache as fallback (stale data)"
---

## 1. What it is

Using a cache as a [fallback](0282-fallback-methods-default-responses.md) means that when a live call to a dependency fails, instead of returning a generic default or an error, the caller returns the *last known good response* it previously cached for that same request — even though that cached value may now be stale (out of date relative to the live source of truth). This trades data freshness for availability: the caller gets a real, specific answer instead of no answer or a made-up generic one.

## 2. Why & when

A generic fallback (like "show popular items" when personalized recommendations fail) works when there is no meaningful per-request cached alternative. But for many kinds of data — a user's profile, a product's price and description, an account balance snapshot — a generic default isn't meaningful at all; the only sensible fallback is "the last value we successfully fetched for this specific thing," even if it's a few minutes or hours old.

Use cache-as-fallback when the data changes slowly relative to how long an outage might last, and when slightly stale data is clearly preferable to no data at all — a product page showing yesterday's price during a brief outage is almost always better than a broken page. Do not use it for data where staleness is actively dangerous or misleading, such as real-time inventory counts used to prevent overselling, or anything where an out-of-date value could cause a user or the system to take an incorrect action.

## 3. Core concept

The cache is populated opportunistically on every successful live call (so it's always as fresh as the last success), and consulted only on failure — the live call is still always attempted first, since fresh data is always preferred when available.

```java
class CacheFallbackClient<T> {
    final java.util.Map<String, T> cache = new java.util.concurrent.ConcurrentHashMap<>();
    final java.util.Map<String, Long> cachedAt = new java.util.concurrent.ConcurrentHashMap<>();

    T get(String key, java.util.function.Supplier<T> liveCall) {
        try {
            T fresh = liveCall.get();
            cache.put(key, fresh); cachedAt.put(key, System.currentTimeMillis()); // REFRESH cache on success
            return fresh;
        } catch (Exception e) {
            T stale = cache.get(key); // FALL BACK to last known good value
            if (stale == null) throw new RuntimeException("no live data and no cached fallback", e);
            return stale; // STALE but AVAILABLE
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Every successful live call refreshes the cache with the new value; when a live call fails, the caller falls back to the last cached value instead of the live one, trading data freshness for availability rather than returning an error">
  <rect x="30" y="20" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">live call</text>

  <line x1="105" y1="60" x2="105" y2="90" stroke="#6db33f" marker-end="url(#arr284)"/>
  <text x="150" y="78" fill="#8b949e" font-size="7" font-family="sans-serif">success: REFRESH cache</text>
  <rect x="30" y="95" width="150" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="105" y="119" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">cache (last known good)</text>

  <line x1="180" y1="40" x2="440" y2="40" stroke="#8b949e" stroke-dasharray="2,2" marker-end="url(#arr284)"/>
  <text x="310" y="30" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">failure: FALL BACK to cache</text>
  <line x1="180" y1="115" x2="440" y2="60" stroke="#8b949e" marker-end="url(#arr284)"/>

  <rect x="440" y="20" width="160" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="520" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">caller gets fresh or stale value</text>

  <defs><marker id="arr284" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Success refreshes the cache; failure falls back to it — the caller always gets a real, specific value when one has ever existed.

## 5. Runnable example

Scenario: a product-price client with no caching that errors out during an outage, extended to cache successful responses and fall back to them on failure, and finally adding staleness awareness — surfacing how old the fallback data is and refusing to use it past a maximum acceptable age, protecting against dangerously outdated fallbacks.

### Level 1 — Basic

```java
// File: NoCacheFailsOnOutage.java -- a live-only client: any failure of
// the live call is a hard failure for the caller, with no fallback.
public class NoCacheFailsOnOutage {
    static int callCount = 0;
    static double getLivePrice(String productId) {
        callCount++;
        if (callCount == 1) return 29.99; // first call succeeds
        throw new RuntimeException("pricing-service unreachable"); // subsequent calls simulate an outage
    }

    public static void main(String[] args) {
        System.out.println("Call 1: $" + getLivePrice("sku-123"));
        try {
            System.out.println("Call 2: $" + getLivePrice("sku-123"));
        } catch (Exception e) {
            System.out.println("Call 2: FAILED -- " + e.getMessage() + " (no fallback available)");
        }
    }
}
```

How to run: `java NoCacheFailsOnOutage.java`

The first call succeeds and returns a price. The second call simulates the pricing service going down and throws. With no caching in place, the caller has nothing to fall back to — the price simply cannot be shown, even though it was successfully fetched moments earlier.

### Level 2 — Intermediate

```java
// File: CacheFallback.java -- the same client, but every successful
// call is cached; a failed call falls back to the cached value instead
// of failing outright.
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Supplier;

public class CacheFallback {
    static int callCount = 0;
    static double getLivePrice(String productId) {
        callCount++;
        if (callCount == 1) return 29.99;
        throw new RuntimeException("pricing-service unreachable");
    }

    static final Map<String, Double> cache = new ConcurrentHashMap<>();

    static double getPriceWithFallback(String productId) {
        try {
            double fresh = getLivePrice(productId);
            cache.put(productId, fresh); // REFRESH on success
            return fresh;
        } catch (Exception e) {
            Double stale = cache.get(productId);
            if (stale == null) throw new RuntimeException("no live price and no cache", e);
            System.out.println("  (live call failed: " + e.getMessage() + " -- falling back to cached price)");
            return stale;
        }
    }

    public static void main(String[] args) {
        System.out.println("Call 1: $" + getPriceWithFallback("sku-123"));
        System.out.println("Call 2: $" + getPriceWithFallback("sku-123"));
        System.out.println("Call 3: $" + getPriceWithFallback("sku-123"));
    }
}
```

How to run: `java CacheFallback.java`

Call 1 succeeds, returns $29.99, and caches it. Calls 2 and 3 hit the simulated outage and fail live, but `getPriceWithFallback` catches the exception and returns the cached $29.99 both times instead of failing. The caller (and ultimately the user) sees a consistent, usable price throughout the outage, even though it's no longer guaranteed to be current.

### Level 3 — Advanced

```java
// File: StalenessAwareCacheFallback.java -- tracks WHEN each cached
// value was captured and refuses to serve a fallback older than a
// configured maximum age, since some data becomes actively dangerous
// once too stale (rather than merely inconvenient).
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.time.Duration;

public class StalenessAwareCacheFallback {
    static int callCount = 0;
    static double getLivePrice(String productId) {
        callCount++;
        if (callCount == 1) return 29.99;
        throw new RuntimeException("pricing-service unreachable");
    }

    record CachedValue(double value, long cachedAtMillis) {}

    static final Map<String, CachedValue> cache = new ConcurrentHashMap<>();
    static final Duration maxAcceptableStaleness = Duration.ofMillis(500);

    static String getPriceWithFallback(String productId, long simulatedNow) {
        try {
            double fresh = getLivePrice(productId);
            cache.put(productId, new CachedValue(fresh, simulatedNow));
            return "$" + fresh + " (fresh)";
        } catch (Exception e) {
            CachedValue stale = cache.get(productId);
            if (stale == null) return "UNAVAILABLE (no live price, no cache)";
            long age = simulatedNow - stale.cachedAtMillis();
            if (age > maxAcceptableStaleness.toMillis()) {
                return "UNAVAILABLE (cached price is " + age + "ms old, exceeds max staleness of "
                        + maxAcceptableStaleness.toMillis() + "ms -- too risky to show)";
            }
            return "$" + stale.value() + " (STALE, " + age + "ms old, within acceptable range)";
        }
    }

    public static void main(String[] args) {
        long t0 = 0;
        System.out.println("t=0ms:    " + getPriceWithFallback("sku-123", t0));
        System.out.println("t=200ms:  " + getPriceWithFallback("sku-123", t0 + 200));   // within staleness budget
        System.out.println("t=900ms:  " + getPriceWithFallback("sku-123", t0 + 900));   // exceeds staleness budget
    }
}
```

How to run: `java StalenessAwareCacheFallback.java`

The price is fetched live at `t=0` and cached with that timestamp. At `t=200ms`, the live call fails, but the cached value is only 200ms old, well within the 500ms `maxAcceptableStaleness`, so it is served with a clear "STALE" label. At `t=900ms`, the live call still fails, and now the cached value is 900ms old — past the configured maximum — so the fallback deliberately refuses to serve it, returning "UNAVAILABLE" instead of a price that might now be dangerously out of date. This is the production-relevant refinement: not all stale data is equally safe to serve, and a maximum staleness bound prevents a long outage from quietly serving increasingly wrong data indefinitely.

## 6. Walkthrough

Trace `StalenessAwareCacheFallback.main` in order. **First**, `getPriceWithFallback("sku-123", 0)` is called. Inside, `getLivePrice` succeeds (call count 1) and returns 29.99. This value is wrapped in a `CachedValue(29.99, 0)` and stored in `cache`. The method returns `"$29.99 (fresh)"`.

**Next**, `getPriceWithFallback("sku-123", 200)` is called. `getLivePrice` now throws (call count 2), landing in the `catch` block. `stale` is retrieved from `cache` — it's the `CachedValue(29.99, 0)` stored a moment ago. `age` is computed as `simulatedNow(200) - stale.cachedAtMillis()(0) = 200`. Since `200 <= 500` (the max acceptable staleness), the method returns the cached value with a `"(STALE, 200ms old...)"` label — the caller still gets a real, specific price, just honestly labeled as not current.

**Finally**, `getPriceWithFallback("sku-123", 900)` is called. `getLivePrice` throws again. The same cached value (still `cachedAtMillis=0`, since no live call has succeeded since) is retrieved, and `age = 900 - 0 = 900`. This time `900 > 500`, so the staleness check fails, and the method returns `"UNAVAILABLE (... too risky to show)"` instead of the stale price — deliberately refusing to show data that has become too old to trust.

**Data transformation across the three calls**: the same underlying cached record (`value=29.99, cachedAtMillis=0`) is reused for both fallback attempts, but the *decision* of whether to serve it changes purely based on how much simulated time has elapsed — the caller-visible outcome shifts from "fresh" to "stale-but-usable" to "unavailable" as staleness crosses the configured threshold, without the cached data itself ever changing.

```
t=0ms   live call OK  -> cache = {value:29.99, at:0}   -> "$29.99 (fresh)"
t=200ms live call FAILS -> age=200ms <= 500ms budget    -> "$29.99 (STALE, 200ms old)"
t=900ms live call FAILS -> age=900ms >  500ms budget    -> "UNAVAILABLE (too risky)"
```

## 7. Gotchas & takeaways

> Not all stale data is safe merely because it's better than nothing — for data where being wrong is actively harmful (real-time inventory, account balances used to authorize a transaction), an unbounded "always fall back to cache" policy can turn a brief outage into a correctness incident. Bound the acceptable staleness explicitly.

- Cache-as-fallback is strictly more useful than a generic fallback when the request has a specific identity (a product ID, a user ID) — it returns the *actual* last-known value for that specific thing, not a made-up substitute.
- Always populate the cache from successful live calls, never let the fallback cache go stale by only writing to it on the fallback path itself.
- Clearly label fallback/stale responses (in logs, metrics, and ideally in the response itself via a header or field) so both operators and, where relevant, end users can distinguish live data from a cached substitute.
- Set an explicit maximum acceptable staleness for any data where being wrong has real consequences, and fail outright once cached data exceeds it rather than serving indefinitely aging data through an extended outage.
