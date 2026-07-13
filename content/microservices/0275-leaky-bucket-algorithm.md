---
card: microservices
gi: 275
slug: leaky-bucket-algorithm
title: "Leaky bucket algorithm"
---

## 1. What it is

The leaky bucket algorithm is an alternative to the [token bucket algorithm](0274-token-bucket-algorithm.md) for rate limiting. Incoming requests are pictured as water poured into a bucket with a small hole in the bottom: the bucket holds a limited amount (its capacity), water leaks out — meaning requests are processed — at a fixed, constant rate no matter how fast it was poured in, and if water is poured in faster than it can leak out, the bucket overflows and the excess is dropped (rejected). The defining property is that the *outflow* rate is always smooth and constant, unlike token bucket where bursts pass through immediately.

## 2. Why & when

Token bucket allows a burst of saved-up tokens to be spent instantly, which is fine when the downstream system can absorb a sudden spike. But some downstream systems — a fixed-capacity worker pool, a legacy service with a hard per-second ceiling, a billing metering pipeline — need requests to arrive at a smooth, predictable rate, not in bursts. Leaky bucket enforces exactly that: no matter how bursty the input is, the output rate is capped and constant.

Use leaky bucket when the goal is traffic *shaping* (smoothing bursty input into a steady, predictable outflow) rather than just capping the average rate while tolerating bursts. It is common in network traffic shaping, queueing systems that feed a fixed-throughput downstream, and any place where a jittery arrival pattern must be turned into a steady one before hitting something fragile.

## 3. Core concept

Requests either sit in a bounded queue (the "bucket") waiting to leak out at a fixed rate, or — in a simpler counter-only variant — a running "water level" increases by 1 per request and decreases at a fixed rate over time; a request is accepted only if the level after adding it would not exceed capacity.

```java
class LeakyBucket {
    double level = 0;              // current WATER level (queued/pending work)
    final double capacity;         // MAXIMUM level before overflow -- BUCKET SIZE
    final double leakRatePerSecond; // fixed OUTFLOW rate -- how fast requests are PROCESSED
    long lastLeakTimeMillis = System.currentTimeMillis();

    boolean tryAdd() {
        leak(); // drain based on ELAPSED time -- constant, steady outflow
        if (level + 1 <= capacity) { level += 1; return true; } // room -- ACCEPTED
        return false; // OVERFLOW -- request REJECTED
    }

    void leak() {
        long now = System.currentTimeMillis();
        double elapsedSeconds = (now - lastLeakTimeMillis) / 1000.0;
        level = Math.max(0, level - elapsedSeconds * leakRatePerSecond); // DRAIN, floored at 0
        lastLeakTimeMillis = now;
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bursty water is poured into a bucket at an irregular rate; the bucket holds a bounded level and overflows excess when full; water leaks out the bottom at a fixed, constant rate, producing a smooth, steady output regardless of how bursty the input was">
  <text x="90" y="20" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">bursty input (irregular)</text>
  <path d="M50,30 L70,50 L60,45 L90,60 L80,55" stroke="#79c0ff" fill="none" stroke-width="1.5"/>
  <line x1="90" y1="60" x2="90" y2="75" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr275)"/>

  <rect x="50" y="80" width="80" height="90" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="58" y="110" width="64" height="60" fill="#6db33f" opacity="0.3"/>
  <text x="90" y="145" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">level</text>
  <text x="90" y="183" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">bounded capacity</text>

  <text x="200" y="60" fill="#8b949e" font-size="7.5" font-family="sans-serif">overflow &#8594; dropped</text>
  <line x1="132" y1="90" x2="200" y2="65" stroke="#8b949e" stroke-dasharray="3,3" marker-end="url(#arr275)"/>

  <line x1="90" y1="170" x2="90" y2="185" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr275)"/>
  <rect x="320" y="145" width="220" height="20" fill="none" stroke="#6db33f"/>
  <circle cx="335" cy="155" r="4" fill="#6db33f"/><circle cx="375" cy="155" r="4" fill="#6db33f"/>
  <circle cx="415" cy="155" r="4" fill="#6db33f"/><circle cx="455" cy="155" r="4" fill="#6db33f"/>
  <circle cx="495" cy="155" r="4" fill="#6db33f"/>
  <line x1="130" y1="155" x2="320" y2="155" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr275)"/>
  <text x="430" y="130" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">smooth, constant outflow (evenly spaced)</text>

  <defs>
    <marker id="arr275" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Bursty input either queues inside the bucket or overflows; the outflow rate itself is always smooth and constant.

## 5. Runnable example

Scenario: a leaky bucket accepting or rejecting requests based on remaining capacity, extended to show it smoothing a burst into a steady drain rate over time, and finally handling a producer that sustains a rate above the leak rate (showing the bucket saturates and starts rejecting, protecting the downstream system).

### Level 1 — Basic

```java
// File: BasicLeakyBucket.java -- accepts requests only while there is
// room under capacity; level drains at a fixed rate over time.
public class BasicLeakyBucket {
    static class LeakyBucket {
        double level = 0;
        final double capacity = 5;
        final double leakRatePerSecond = 2;
        long lastLeakTimeMillis = System.currentTimeMillis();

        boolean tryAdd() {
            leak();
            if (level + 1 <= capacity) { level += 1; return true; }
            return false;
        }
        void leak() {
            long now = System.currentTimeMillis();
            double elapsedSeconds = (now - lastLeakTimeMillis) / 1000.0;
            level = Math.max(0, level - elapsedSeconds * leakRatePerSecond);
            lastLeakTimeMillis = now;
        }
    }

    public static void main(String[] args) {
        LeakyBucket bucket = new LeakyBucket();
        for (int i = 1; i <= 7; i++) {
            boolean accepted = bucket.tryAdd();
            System.out.println("Request " + i + ": " + (accepted ? "ACCEPTED" : "REJECTED (bucket full, level=" + bucket.level + ")"));
        }
    }
}
```

How to run: `java BasicLeakyBucket.java`

This fires seven requests back-to-back with no delay between them, so the bucket has no time to leak. Capacity is 5, so the first five are accepted (level climbs 1, 2, 3, 4, 5) and the sixth and seventh are rejected because the level would exceed capacity. This demonstrates the overflow-on-burst behavior: leaky bucket does not let a burst straight through the way token bucket does — it only accepts what fits in the bounded queue.

### Level 2 — Intermediate

```java
// File: SmoothingLeakyBucket.java -- same bucket, but now a background
// "worker" drains (processes) queued requests at the fixed leak rate,
// showing bursty arrivals turned into a steady, evenly spaced outflow.
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class SmoothingLeakyBucket {
    static class LeakyBucket {
        double level = 0;
        final double capacity = 5;
        final double leakRatePerSecond = 2; // processes 1 request every 500ms
        long lastLeakTimeMillis = System.currentTimeMillis();

        synchronized boolean tryAdd() {
            leak();
            if (level + 1 <= capacity) { level += 1; return true; }
            return false;
        }
        synchronized void leak() {
            long now = System.currentTimeMillis();
            double elapsedSeconds = (now - lastLeakTimeMillis) / 1000.0;
            level = Math.max(0, level - elapsedSeconds * leakRatePerSecond);
            lastLeakTimeMillis = now;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        LeakyBucket bucket = new LeakyBucket();
        AtomicInteger processed = new AtomicInteger(0);

        // Burst: 5 requests arrive instantly.
        for (int i = 1; i <= 5; i++) {
            System.out.println("Enqueue " + i + ": " + (bucket.tryAdd() ? "ACCEPTED (queued)" : "REJECTED"));
        }

        // Worker "processes" (drains) at the fixed leak rate: 1 every 500ms.
        ScheduledExecutorService worker = Executors.newSingleThreadScheduledExecutor();
        worker.scheduleAtFixedRate(() -> {
            bucket.leak();
            System.out.printf("Worker tick: level now %.2f (steady drain)%n", bucket.level);
        }, 500, 500, TimeUnit.MILLISECONDS);

        Thread.sleep(2600);
        worker.shutdown();
    }
}
```

How to run: `java SmoothingLeakyBucket.java`

The five requests arrive in a burst and are all queued instantly (accepted, since 5 fits in capacity). The change from Level 1 is the addition of a scheduled worker that ticks every 500ms — matching the leak rate of 2/second — and calls `leak()` to drain the level. Watching the output, the burst of arrivals happens instantly, but the *processing* happens smoothly and evenly spaced, one drain step at a time, regardless of how clumped the arrivals were. This is the real-world value of leaky bucket: it decouples a bursty producer from a downstream consumer that must never see anything but a steady rate.

### Level 3 — Advanced

```java
// File: SustainedOverloadLeakyBucket.java -- a producer that sustains a
// rate HIGHER than the leak rate for a long time. Shows the bucket
// saturating and steadily rejecting the excess, protecting the downstream
// system from ever seeing more than the constant leak rate.
import java.util.concurrent.atomic.AtomicInteger;

public class SustainedOverloadLeakyBucket {
    static class LeakyBucket {
        double level = 0;
        final double capacity;
        final double leakRatePerSecond;
        long lastLeakTimeMillis = System.currentTimeMillis();

        LeakyBucket(double capacity, double leakRatePerSecond) {
            this.capacity = capacity;
            this.leakRatePerSecond = leakRatePerSecond;
        }

        synchronized boolean tryAdd() {
            leak();
            if (level + 1 <= capacity) { level += 1; return true; }
            return false;
        }
        synchronized void leak() {
            long now = System.currentTimeMillis();
            double elapsedSeconds = (now - lastLeakTimeMillis) / 1000.0;
            level = Math.max(0, level - elapsedSeconds * leakRatePerSecond);
            lastLeakTimeMillis = now;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        LeakyBucket bucket = new LeakyBucket(10, 5); // capacity 10, leaks 5/sec (processes 5 req/sec)
        AtomicInteger accepted = new AtomicInteger(0);
        AtomicInteger rejected = new AtomicInteger(0);

        // Producer sustains 20 requests/sec for 2 seconds -- FOUR TIMES the leak rate.
        long start = System.currentTimeMillis();
        long durationMillis = 2000;
        int producerIntervalMillis = 50; // ~20 req/sec

        while (System.currentTimeMillis() - start < durationMillis) {
            if (bucket.tryAdd()) accepted.incrementAndGet(); else rejected.incrementAndGet();
            Thread.sleep(producerIntervalMillis);
        }

        double elapsedSeconds = (System.currentTimeMillis() - start) / 1000.0;
        System.out.printf("Elapsed: %.2fs%n", elapsedSeconds);
        System.out.println("Accepted: " + accepted + "  Rejected: " + rejected.get());
        System.out.printf("Effective accepted rate: %.2f req/sec (leak rate cap was %.0f)%n",
                accepted.get() / elapsedSeconds, bucket.leakRatePerSecond);
    }
}
```

How to run: `java SustainedOverloadLeakyBucket.java`

This models a sustained overload: the producer offers roughly 20 requests/second for 2 seconds, but the bucket's leak rate caps processing at 5/second with a capacity of only 10. Once the bucket fills (after about half a second), further requests are rejected almost as fast as they arrive, because the drain can only free up 5 slots/second while the producer wants 20. The final printed "effective accepted rate" converges toward the configured leak rate, not the offered rate — proving the bucket enforces a hard, constant ceiling on throughput regardless of how much pressure is applied upstream. This is the production-relevant behavior: a downstream service protected by a leaky bucket never sees more than its configured steady-state capacity, even under sustained, heavy overload.

## 6. Walkthrough

Trace the Level 3 program end to end. **First**, the bucket is constructed with `capacity=10` and `leakRatePerSecond=5`, and `lastLeakTimeMillis` is set to the current time.

**Next**, the producer loop begins: every 50ms it calls `tryAdd()`. Inside `tryAdd()`, `leak()` runs first — it computes elapsed time since the last leak check, subtracts `elapsedSeconds * 5` from `level`, and floors at 0. Immediately after, `tryAdd()` checks whether `level + 1 <= capacity`; if so it increments `level` and returns `true` (accepted), otherwise it returns `false` (rejected) without changing `level`.

**Early on** (first ~0.5 seconds), the bucket is empty and each new request adds roughly 1 to the level while only a small amount leaks out between calls (since leak rate is 5/sec but requests arrive every 50ms = 20/sec) — so the level climbs quickly toward 10.

**Once saturated**, each subsequent `tryAdd()` call still runs `leak()` first (draining a small amount based on the 50ms gap — about 0.25 tokens' worth), but that tiny drain is rarely enough to bring `level + 1` back under 10, so most calls return `false` and are counted as rejected. Only occasionally, when enough time has passed since the last successful drain, does a slot free up and a request get accepted.

**At the end** of the 2-second loop, the program computes the elapsed wall-clock time and divides the accepted count by it to get the effective throughput. Because the bucket structurally cannot accept more than `leakRatePerSecond` requests per second once it's saturated, this effective rate converges to approximately 5/sec — matching the configured leak rate — even though the producer offered roughly 20/sec the entire time.

```
Offered rate:  20 req/sec  ─┐
                             ├─▶ [ Leaky Bucket cap=10, leak=5/sec ] ─▶ Accepted ≈ 5 req/sec
                             │        (excess rejected once full)
                            (burst absorbed briefly, then overflow)
```

Sample output shape:
```
Elapsed: 2.01s
Accepted: 11  Rejected: 29
Effective accepted rate: 5.47 req/sec (leak rate cap was 5)
```

This is the key state transformation across the run: raw offered load (bursty, 20/sec) enters the bucket, the bucket's bounded `level` state absorbs a brief initial burst, and once saturated the bucket's fixed drain rate reshapes everything downstream into a steady ≈5/sec — the defining trait of leaky bucket versus token bucket, where a burst would instead pass straight through up to the bucket's full capacity.

## 7. Gotchas & takeaways

> Leaky bucket smooths *output*, token bucket tolerates *input* bursts — picking the wrong one for your use case either needlessly rejects legitimate bursts or lets bursts through to a system that cannot handle them.

- Leaky bucket enforces a hard, constant outflow rate; it never lets a burst through faster than the leak rate, unlike token bucket.
- The queue-based variant (a literal bounded queue processed by a worker) adds latency for queued requests, since they wait their turn; the counter-only variant (shown here) instead rejects immediately when full, adding no latency but no queuing benefit either.
- Choose leaky bucket when downstream capacity is fixed and bursts would overwhelm it (e.g., a worker pool, a hardware-rate-limited API); choose token bucket when bursts are fine as long as the long-term average is bounded.
- As with token bucket, a distributed leaky bucket needs shared state (e.g., Redis) across instances — a per-instance-only bucket under-enforces the true limit when there are multiple app instances behind a load balancer.
