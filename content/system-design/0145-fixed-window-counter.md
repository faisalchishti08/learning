---
card: system-design
gi: 145
slug: fixed-window-counter
title: Fixed-window counter
---

## 1. What it is

The **fixed-window counter** algorithm divides time into fixed-size windows (e.g. every 60 seconds) and counts how many requests a client makes within the current window. Once the count reaches the limit, further requests in that same window are rejected. When the window ends, the counter resets to zero and a fresh window begins. It works like a ticket booth that only sells 100 tickets per hour, then locks the window and reopens it, freshly restocked, at the top of the next hour.

## 2. Why & when

A fixed-window counter is the simplest possible rate limiter: one integer counter and one timestamp per client, checked and incremented on every request. It is cheap to implement and reason about, and works well when you only need an approximate cap on requests per time period, and do not need a perfectly smooth rate. Use it for simple internal quotas or first-pass API protection, where implementation simplicity matters more than precision — but be aware of its boundary-burst weakness, covered below.

## 3. Core concept

- **Window size:** a fixed duration, such as 1 minute; the current window is determined by dividing the current time by the window size (e.g. `windowStart = (now / windowSizeMillis) * windowSizeMillis`).
- **Per-window counter:** a single integer, incremented on every request that falls inside the current window.
- **Reset on window change:** when a request arrives in a new window (its computed `windowStart` differs from the stored one), the counter resets to zero before counting that request.
- **Limit check:** if the counter would exceed the configured limit, the request is rejected; otherwise it is allowed and the counter increments.
- **The boundary-burst problem:** because the counter fully resets at the window edge, a client can send the full limit right at the very end of one window, then immediately send the full limit again right at the start of the next — twice the intended limit in a very short real time span, even though each window individually stayed under the cap.

## 4. Diagram

```
   window 1 [0s -------------------- 60s]   window 2 [60s ------------------- 120s]
              ^                        ^      ^
              |                        |      |
        counter resets to 0      59.9s: 100   60.1s: counter resets to 0 again,
                                  requests     100 MORE requests allowed instantly
                                  allowed
                                  (at the limit)
              \_______________________/\_________________________/
                     up to 200 requests can land in this ~0.2s span,
                     even though the limit is "100 per window"
```
*Caption: the counter resets sharply at each window boundary, so a client can double up right at the edge between two windows.*

## 5. Runnable example

**Level 1 — Basic.** A single counter with a limit, reset manually.

**Level 2 — Time-based windows.** Compute the current window from a timestamp and reset automatically when the window changes.

**Level 3 — Demonstrate the boundary-burst weakness.** Show a client legally sending double the per-window limit across a window boundary.

```java
// FixedWindowCounterDemo.java
public class FixedWindowCounterDemo {

    static class FixedWindowLimiter {
        final int limit;
        final long windowSizeMillis;
        long currentWindowStart;
        int count;

        FixedWindowLimiter(int limit, long windowSizeMillis) {
            this.limit = limit;
            this.windowSizeMillis = windowSizeMillis;
            this.currentWindowStart = -1;
        }

        // Level 2: figure out which window "now" belongs to, resetting on change.
        boolean allow(long nowMillis) {
            long windowStart = (nowMillis / windowSizeMillis) * windowSizeMillis;
            if (windowStart != currentWindowStart) {
                currentWindowStart = windowStart;
                count = 0; // Level 1: reset the counter for the new window
            }
            if (count >= limit) {
                return false;
            }
            count++;
            return true;
        }
    }

    public static void main(String[] args) {
        // limit 3 requests per 1000ms window
        FixedWindowLimiter limiter = new FixedWindowLimiter(3, 1000);

        // Level 3: send 3 requests right at the end of window 1 (t=900..990ms)...
        long[] windowOneTimestamps = {900, 950, 990};
        for (long t : windowOneTimestamps) {
            System.out.println("t=" + t + "ms (window 1): " + (limiter.allow(t) ? "ALLOWED" : "REJECTED"));
        }

        // ...then 3 MORE requests right at the start of window 2 (t=1005..1050ms).
        long[] windowTwoTimestamps = {1005, 1020, 1050};
        for (long t : windowTwoTimestamps) {
            System.out.println("t=" + t + "ms (window 2): " + (limiter.allow(t) ? "ALLOWED" : "REJECTED"));
        }
        System.out.println("6 requests allowed within a ~150ms span, despite a limit of 3 per 1000ms window.");
    }
}
```

**How to run:** save as `FixedWindowCounterDemo.java`, then run `java FixedWindowCounterDemo.java`.

## 6. Walkthrough

1. For `t=900`, `allow` computes `windowStart = (900 / 1000) * 1000 = 0`; since `currentWindowStart` starts at `-1`, it resets `count` to 0, then allows the request and sets `count = 1`.
2. `t=950` and `t=990` both compute the same `windowStart = 0`, so no reset happens; `count` climbs to 2, then 3, and both are allowed since `count < limit` at the time of each check.
3. For `t=1005`, `allow` computes `windowStart = (1005 / 1000) * 1000 = 1000`, which differs from the stored `currentWindowStart` of `0`; this triggers a reset of `count` back to 0 before checking the limit, so the request is allowed even though window 1's count had already reached the limit moments earlier.
4. `t=1020` and `t=1050` also fall in `windowStart = 1000`, and since `count` only just reset, both are allowed too, bringing the total to 3 more requests.
5. All 6 requests across both windows are printed as "ALLOWED", even though only roughly 150 milliseconds of real time separate the first and last request — the fixed window's hard reset at the boundary let a full second window's worth of traffic through twice in quick succession, which is exactly the weakness a [sliding window](0146-sliding-window-log-sliding-window-counter.md) approach fixes.

## 7. Gotchas & takeaways

> Gotcha: the boundary-burst problem is not a bug in this implementation — it is inherent to the fixed-window algorithm itself. Any fixed-window counter can be pushed to roughly double its stated limit by a client timing its requests around a window edge, so never use it where a hard, precise cap actually matters.

- A fixed-window counter is simple: one integer and one window-start timestamp, reset when the window changes.
- Its simplicity is also its weakness: a client can burst up to double the limit across a window boundary.
- It is a reasonable choice for loose, approximate quotas, but not for strict rate enforcement.
- Related concepts: [Sliding-window log & sliding-window counter](0146-sliding-window-log-sliding-window-counter.md) (fixes the boundary-burst problem), [Token bucket](0143-token-bucket.md) (allows controlled bursts by design instead of by accident), [Per-user vs global quotas](0148-per-user-vs-global-quotas.md) (deciding what a counter like this should be keyed by).
