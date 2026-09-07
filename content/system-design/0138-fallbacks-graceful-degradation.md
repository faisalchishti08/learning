---
card: system-design
gi: 138
slug: fallbacks-graceful-degradation
title: Fallbacks & graceful degradation
---

## 1. What it is

A **fallback** is an alternative response or action a caller takes when its primary call fails — a cached copy of the data, a simplified default value, or a completely different (but still useful) response — instead of simply propagating the failure to the end user. This is the concrete mechanism behind graceful degradation: rather than a page failing to load at all because one non-essential dependency is down, a fallback lets the page load successfully with that one part simplified or omitted.

## 2. Why & when

A [circuit breaker](0136-circuit-breaker.md) tripping open, or a call exceeding its [timeout](0134-timeouts.md), tells you a call has failed — but the caller still needs to decide what to actually show the user or do next. Without a fallback, that decision defaults to "fail the whole request," which is often a worse outcome than necessary, especially when the failed part was not essential to the core value of the response. Define a fallback for any dependency whose failure should not block the overall request from still succeeding in a reduced form — the more essential a dependency actually is, the harder it is to find a good fallback for it, which is itself useful information about your system's true dependency structure.

## 3. Core concept

- **Cached fallback:** return the last successfully fetched value from a cache, even if it might be somewhat stale, rather than nothing at all — appropriate when slightly outdated data is better than no data.
- **Default value fallback:** return a safe, generic default (an empty list, a zero count, a "recommendations unavailable" message) when there is no reasonable cached value to fall back to.
- **Degraded-functionality fallback:** skip an entire non-essential feature of the response (as in the [load shedding & graceful degradation](0124-load-shedding-graceful-degradation.md) example) while still returning everything else successfully.
- **Fallback chains:** a fallback can itself fail and need its own fallback (try live data, then cached data, then a static default) — but this chain must terminate in something that cannot itself fail, or the whole point is lost.
- **Fallbacks change what "success" means for that call:** the calling code must clearly track whether a fallback was used, both to report it (metrics, logging) and because some callers of *that* code may need to know the data is not fully live.

## 4. Diagram

```
Primary call to Recommendations Service: FAILS (circuit breaker open)
              |
              v
     Try fallback 1: cached recommendations from 10 minutes ago
              |
     cache also empty (never populated for this user)
              |
              v
     Try fallback 2: static default ("Popular items" list, not personalized)
              |
              v
     ALWAYS succeeds - the final fallback cannot itself fail

Result: page loads successfully, with generic "Popular items"
instead of a personalized (but currently unavailable) list.
```
*Caption: a fallback chain tries progressively simpler alternatives, terminating in something guaranteed to succeed, so the overall request still completes.*

## 5. Runnable example

**Level 1 — Basic.** A primary call fails; fall back to a cached value.

**Level 2 — Fallback chain.** The cache is also empty; fall further back to a static default that cannot fail.

**Level 3 — Tracking fallback usage.** Record whether a fallback was used, so the caller and monitoring both know the data is not fully live.

```java
// FallbacksDemo.java
import java.util.*;

public class FallbacksDemo {

    record Result(List<String> items, String source) {}

    static List<String> callRecommendationsService(boolean serviceHealthy) {
        if (!serviceHealthy) throw new RuntimeException("recommendations service unavailable");
        return List.of("Personalized Item A", "Personalized Item B");
    }

    static Map<String, List<String>> recommendationsCache = new HashMap<>();

    static Result getRecommendationsWithFallback(String userId, boolean serviceHealthy) {
        try {
            List<String> live = callRecommendationsService(serviceHealthy);
            recommendationsCache.put(userId, live); // update cache on success, for future fallback use
            return new Result(live, "live");
        } catch (RuntimeException primaryFailure) {
            System.out.println("primary call failed: " + primaryFailure.getMessage() + " - trying fallback 1 (cache)");
            List<String> cached = recommendationsCache.get(userId);
            if (cached != null) {
                return new Result(cached, "cache");
            }
            System.out.println("cache also empty for this user - trying fallback 2 (static default)");
            List<String> staticDefault = List.of("Popular Item X", "Popular Item Y"); // cannot fail
            return new Result(staticDefault, "static-default");
        }
    }

    public static void main(String[] args) {
        // Level 1: service healthy - live call succeeds, and populates the cache.
        Result result1 = getRecommendationsWithFallback("user-1", true);
        System.out.println("user-1, service healthy: " + result1);

        // Level 1 continued: same user, service now DOWN - falls back to the cache populated above.
        Result result2 = getRecommendationsWithFallback("user-1", false);
        System.out.println("user-1, service down: " + result2);

        // Level 2: a DIFFERENT user with no cached entry, service also down - falls all the way to static default.
        Result result3 = getRecommendationsWithFallback("user-2-never-seen-before", false);
        System.out.println("user-2, service down, no cache entry: " + result3);

        // Level 3: track fallback usage for monitoring - alert if fallback rate is too high.
        List<Result> recentResults = List.of(result1, result2, result3);
        long fallbackCount = recentResults.stream().filter(r -> !r.source().equals("live")).count();
        double fallbackRate = 100.0 * fallbackCount / recentResults.size();
        System.out.printf("fallback usage rate: %.1f%% (%d of %d requests did not use live data)%n",
            fallbackRate, fallbackCount, recentResults.size());
        if (fallbackRate > 50) System.out.println("ALERT: majority of requests are degraded - investigate the primary dependency");
    }
}
```

**How to run:** save as `FallbacksDemo.java`, then run `java FallbacksDemo.java`.

## 6. Walkthrough

1. `getRecommendationsWithFallback("user-1", true)` calls the live service successfully, returns a `Result` tagged `"live"`, and populates `recommendationsCache` for `"user-1"` as a side effect of the successful call.
2. Calling it again for the same user with `serviceHealthy = false` triggers the `catch` block; `recommendationsCache.get("user-1")` finds the entry cached moments earlier, so the function returns that cached list, tagged `"cache"` — fallback 1 succeeded.
3. Calling it for `"user-2-never-seen-before"` with the service also down goes through the same `catch` block, but this time `recommendationsCache.get(...)` returns `null`, since this user was never cached.
4. The code proceeds to fallback 2, `staticDefault`, a hardcoded list with no dependency on anything that could fail — this call always succeeds, tagged `"static-default"`, guaranteeing the overall request still completes even in the worst case.
5. Level 3 collects the three results and counts how many were *not* tagged `"live"`; the computed `fallbackRate` (about 67% in this example, since two of three used a fallback) demonstrates the kind of monitoring signal a real system should track — a high fallback rate is a clear, actionable indicator that the primary dependency needs attention, even though every individual request still technically "succeeded."

## 7. Gotchas & takeaways

> Gotcha: a fallback that quietly succeeds with degraded or stale data, with no visibility into how often it is being used, can mask a real, ongoing dependency outage from ever being noticed or fixed — the system looks "fine" from the outside (every request still returns a 200) while actually serving degraded results to a large fraction of users. Always track and alert on fallback usage rate, not just overall request success rate.

- A fallback provides an alternative, still-useful response when a primary call fails, turning what would be a total failure into a successful, if reduced, result.
- Fallback chains should progress from richer alternatives (a cache) to a guaranteed-to-succeed final default, ensuring the overall request always completes.
- Tracking how often fallbacks are actually used is essential — a system can appear fully healthy by request-success metrics alone while silently serving degraded data to most users.
- Related concepts: [Circuit breaker](0136-circuit-breaker.md) (commonly the trigger that routes a call to its fallback), [Load shedding & graceful degradation](0124-load-shedding-graceful-degradation.md) (the broader principle this mechanism implements).
