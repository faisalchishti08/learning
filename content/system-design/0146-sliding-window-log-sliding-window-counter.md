---
card: system-design
gi: 146
slug: sliding-window-log-sliding-window-counter
title: Sliding-window log & sliding-window counter
---

## 1. What it is

A **sliding-window log** rate limiter stores the exact timestamp of every request a client made, and counts how many of those timestamps fall within the last window duration (e.g. the last 60 seconds), measured from right now, not from a fixed clock boundary. A **sliding-window counter** is a cheaper approximation: it keeps two fixed-window counters (the current one and the previous one) and blends them, weighted by how far into the current window "now" is. Both fix the boundary-burst problem of the plain [fixed-window counter](0145-fixed-window-counter.md).

## 2. Why & when

The fixed-window counter can let a client send up to double its limit by timing requests around a window edge, because the window boundary is fixed by the clock, not by the client's actual request history. A sliding window instead always looks back exactly one window duration from the current moment, so there is no fixed edge to exploit. Use the exact log when you need precise enforcement and can afford to store per-request timestamps (or use it for a low-traffic, high-value limiter); use the counter approximation when you need something cheap and close enough, especially at high request volume where storing every timestamp would be wasteful.

## 3. Core concept

- **Sliding-window log — store timestamps:** on each request, append the current timestamp to a per-client list (or sorted structure), then remove any timestamps older than `now - windowSize`.
- **Sliding-window log — count and compare:** if the remaining count of timestamps is at or above the limit, reject the request; otherwise allow it and keep the new timestamp.
- **Sliding-window log — cost:** this is exact, but memory grows with the number of requests within a window, and every check must prune old entries.
- **Sliding-window counter — two buckets:** keep a counter for the current fixed window and the immediately previous one.
- **Sliding-window counter — weighted estimate:** estimate the count in the trailing window as `previousWindowCount * (1 - elapsedFractionOfCurrentWindow) + currentWindowCount`, which approximates how many of the previous window's requests would still count if you slid the window back exactly one duration.

## 4. Diagram

```
   now = 90s, window = 60s -> sliding window covers [30s, 90s]

   fixed windows:     [0s -------- 60s][60s -------- 120s]
                             prev              current
                          count = 80          count = 20
                                  ^
                      "now" is 30s into the current window (30/60 = 50%)

   sliding estimate = prev * (1 - 0.5) + current
                     = 80 * 0.5 + 20
                     = 60   <- close to the true count of requests in [30s, 90s]
```
*Caption: the counter version blends a fraction of the previous fixed window with all of the current one, approximating the exact log without storing every timestamp.*

## 5. Runnable example

**Level 1 — Basic.** Sliding-window log: store timestamps, prune old ones, and compare against the limit.

**Level 2 — Sliding-window counter.** Approximate the same behavior using only two integer counters instead of a growing list.

**Level 3 — Compare both against the fixed-window boundary-burst scenario.** Show that both correctly reject the burst that a fixed window would have allowed.

```java
// SlidingWindowDemo.java
import java.util.*;

public class SlidingWindowDemo {

    // Level 1: exact sliding-window log.
    static class SlidingWindowLog {
        final int limit;
        final long windowMillis;
        final Deque<Long> timestamps = new ArrayDeque<>();

        SlidingWindowLog(int limit, long windowMillis) {
            this.limit = limit;
            this.windowMillis = windowMillis;
        }

        boolean allow(long now) {
            while (!timestamps.isEmpty() && timestamps.peekFirst() <= now - windowMillis) {
                timestamps.removeFirst(); // prune anything outside the trailing window
            }
            if (timestamps.size() >= limit) {
                return false;
            }
            timestamps.addLast(now);
            return true;
        }
    }

    // Level 2: approximate sliding-window counter using two fixed windows.
    static class SlidingWindowCounter {
        final int limit;
        final long windowMillis;
        long previousWindowStart = -1, currentWindowStart = -1;
        int previousCount = 0, currentCount = 0;

        SlidingWindowCounter(int limit, long windowMillis) {
            this.limit = limit;
            this.windowMillis = windowMillis;
        }

        boolean allow(long now) {
            long windowStart = (now / windowMillis) * windowMillis;
            if (windowStart != currentWindowStart) {
                previousWindowStart = currentWindowStart;
                previousCount = (windowStart - currentWindowStart == windowMillis) ? currentCount : 0;
                currentWindowStart = windowStart;
                currentCount = 0;
            }
            double elapsedFraction = (now - currentWindowStart) / (double) windowMillis;
            double estimate = previousCount * (1 - elapsedFraction) + currentCount;
            if (estimate >= limit) {
                return false;
            }
            currentCount++;
            return true;
        }
    }

    public static void main(String[] args) {
        // Level 3: reproduce the fixed-window boundary-burst scenario (limit 3 per 1000ms).
        System.out.println("-- sliding-window log --");
        SlidingWindowLog log = new SlidingWindowLog(3, 1000);
        long[] burst = {900, 950, 990, 1005, 1020, 1050};
        for (long t : burst) System.out.println("t=" + t + "ms: " + (log.allow(t) ? "ALLOWED" : "REJECTED"));

        System.out.println("-- sliding-window counter --");
        SlidingWindowCounter counter = new SlidingWindowCounter(3, 1000);
        for (long t : burst) System.out.println("t=" + t + "ms: " + (counter.allow(t) ? "ALLOWED" : "REJECTED"));
    }
}
```

**How to run:** save as `SlidingWindowDemo.java`, then run `java SlidingWindowDemo.java`.

## 6. Walkthrough

1. In `SlidingWindowLog`, requests at `t=900`, `950`, `990` each call `allow`; the pruning `while` loop finds nothing older than `now - 1000` yet, so all three are added to `timestamps`, growing it to size 3, and all are allowed.
2. At `t=1005`, `allow` prunes any timestamp `<= 1005 - 1000 = 5`; none qualify (900, 950, 990 are all greater than 5), so `timestamps.size()` is still 3, which is `>= limit`, and the request is correctly rejected — unlike the fixed-window version, the log looks back a full 1000ms from `now`, not from a fixed clock boundary, so it still "sees" the earlier burst.
3. `t=1020` and `t=1050` are rejected the same way, since the earlier timestamps still fall within their respective trailing windows.
4. In `SlidingWindowCounter`, the first window change happens at `t=1005` (crossing from `windowStart=0` to `windowStart=1000`); `previousCount` is set to the prior `currentCount` (3, since all of 900/950/990 landed in window `[0,1000)`), and `currentCount` resets to 0.
5. At `t=1005`, `elapsedFraction = (1005 - 1000) / 1000 = 0.005`, so `estimate = 3 * (1 - 0.005) + 0 ≈ 2.985`, which is just under the limit of 3 — this one request is actually allowed by the approximation, showing it is a close but not perfectly exact match to the log; by `t=1020` and `t=1050`, `currentCount` has risen enough that `estimate` clears the limit and both are rejected, matching the exact log's outcome for those two.

## 7. Gotchas & takeaways

> Gotcha: a sliding-window log's memory use grows with request volume inside the window — a client sending thousands of requests per second needs thousands of stored timestamps per window, per client, which does not scale cheaply. The sliding-window counter avoids this by using only two integers, at the cost of being an approximation rather than an exact count.

- Both sliding-window approaches fix the fixed window's boundary-burst weakness by always looking back exactly one window duration from now, not from a fixed clock edge.
- The log is exact but memory-heavy; the counter is an approximation but needs only two integers per client.
- The counter's estimate can very slightly over- or under-count near a window boundary, which is an acceptable tradeoff for most rate-limiting use cases.
- Related concepts: [Fixed-window counter](0145-fixed-window-counter.md) (the simpler, boundary-vulnerable baseline), [Centralized counter (Redis) rate limiting](0147-centralized-counter-redis-rate-limiting.md) (where these counters actually live in a distributed system), [Token bucket](0143-token-bucket.md) (an alternative that allows bursts by design).
