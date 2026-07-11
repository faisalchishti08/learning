---
card: spring-cloud
gi: 69
slug: resilience4j-implementation
title: "Resilience4j implementation"
---

## 1. What it is

Resilience4j is the concrete library actually implementing the Spring Cloud Circuit Breaker abstraction from the previous card (and the earlier Gateway `CircuitBreaker` filter, and Feign's circuit breaker integration) — a lightweight, functional-programming-oriented resilience toolkit providing not just circuit breaking, but the full family of resilience patterns covered across this section: bulkhead, rate limiter, retry, and time limiter, each independently usable and composable.

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-circuitbreaker-resilience4j</artifactId>
</dependency>
```

```properties
resilience4j.circuitbreaker.instances.billing-service.sliding-window-size=10
resilience4j.circuitbreaker.instances.billing-service.failure-rate-threshold=50
resilience4j.circuitbreaker.instances.billing-service.wait-duration-in-open-state=10s
```

## 2. Why & when

The earlier cards used circuit breaking conceptually, through the vendor-neutral abstraction; this card is about Resilience4j specifically — its actual configuration properties, its sliding-window failure tracking (a genuine improvement over the simplified fixed-count window used in earlier cards' examples), and how it names and configures each protected "instance" independently.

Understanding Resilience4j directly matters because:

- Its configuration properties (`resilience4j.circuitbreaker.instances.*`, and the equivalent for bulkhead/ratelimiter/retry/timelimiter) are what actually gets tuned in a real application — the abstraction layer above it doesn't expose this level of detail.
- Its sliding window can be count-based (last N calls) or time-based (last N seconds) — a real, consequential configuration choice depending on whether a service's traffic is steady or bursty.
- Each protected operation gets its own named "instance" with independent configuration and independent state — `billing-service` and `promotions-service` can have completely different thresholds, tuned to their own actual failure characteristics.

## 3. Core concept

```
 resilience4j.circuitbreaker.instances.<name>.<property>

 sliding-window-type: COUNT_BASED (last N calls) or TIME_BASED (last N seconds)
 sliding-window-size: N
 failure-rate-threshold: percentage (e.g. 50 = trip at 50% failure rate within the window)
 wait-duration-in-open-state: how long to stay OPEN before trying HALF_OPEN
 permitted-number-of-calls-in-half-open-state: how many trial calls before deciding CLOSED or OPEN
```

Each named instance is independently configured and independently tracks its own failure window — `billing-service`'s circuit breaker knows nothing about `promotions-service`'s.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A count based sliding window keeps the most recent N call outcomes while a time based sliding window keeps outcomes from the most recent N seconds, each independently configured per named circuit breaker instance">
  <rect x="20" y="20" width="290" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">COUNT_BASED window</text>
  <text x="165" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">keeps the last N calls</text>
  <text x="165" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">good for steady traffic rates</text>

  <rect x="330" y="20" width="290" height="70" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="475" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">TIME_BASED window</text>
  <text x="475" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">keeps calls from the last N seconds</text>
  <text x="475" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">good for bursty/uneven traffic rates</text>

  <text x="320" y="130" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">each named instance (billing-service, promotions-service, ...) picks its own window type independently</text>

  <defs><marker id="a69" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Count-based and time-based windows answer the same question — "what's the recent failure rate?" — differently depending on how traffic actually arrives.

## 5. Runnable example

The scenario: implement Resilience4j-style sliding window failure tracking for `billing-service`. Start with a count-based window, then add a time-based window and show why it behaves differently under bursty traffic, then run two independently-configured named instances side by side.

### Level 1 — Basic

Count-based sliding window: track the last N call outcomes regardless of when they happened.

```java
import java.util.*;

public class Resilience4jLevel1 {
    static class CountBasedWindow {
        Deque<Boolean> outcomes = new ArrayDeque<>();
        int size;
        double failureRateThreshold;

        CountBasedWindow(int size, double failureRateThreshold) {
            this.size = size; this.failureRateThreshold = failureRateThreshold;
        }

        void record(boolean failed) {
            outcomes.addLast(failed);
            if (outcomes.size() > size) outcomes.removeFirst();
        }

        boolean shouldTrip() {
            if (outcomes.size() < size) return false; // window not full yet -- not enough data
            long failures = outcomes.stream().filter(b -> b).count();
            return (double) failures / size * 100 >= failureRateThreshold;
        }
    }

    public static void main(String[] args) {
        CountBasedWindow window = new CountBasedWindow(5, 50); // trip at 50% failure rate over last 5 calls

        boolean[] outcomes = {true, false, true, true, false}; // 3 failures out of 5 = 60%
        for (boolean failed : outcomes) {
            window.record(failed);
        }
        System.out.println("should trip: " + window.shouldTrip()); // true -- 60% >= 50%
    }
}
```

How to run: `java Resilience4jLevel1.java`

`CountBasedWindow` tracks exactly the last `size` outcomes, regardless of how much time elapsed between them — this is `sliding-window-type: COUNT_BASED`, the default, well suited to services with a fairly steady, predictable call rate where "the last 5 calls" and "the last few seconds" are roughly the same thing.

### Level 2 — Intermediate

Add a time-based window and show why it can behave differently from count-based under bursty traffic — a scenario where a handful of failures within a burst matter more than the same count spread over a long, quiet period.

```java
import java.util.*;

public class Resilience4jLevel2 {
    record Outcome(boolean failed, long timestampMs) {}

    static class TimeBasedWindow {
        List<Outcome> outcomes = new ArrayList<>();
        long windowDurationMs;
        double failureRateThreshold;

        TimeBasedWindow(long windowDurationMs, double failureRateThreshold) {
            this.windowDurationMs = windowDurationMs; this.failureRateThreshold = failureRateThreshold;
        }

        void record(boolean failed, long nowMs) {
            outcomes.add(new Outcome(failed, nowMs));
            outcomes.removeIf(o -> nowMs - o.timestampMs() > windowDurationMs); // drop anything outside the window
        }

        boolean shouldTrip(long nowMs) {
            List<Outcome> inWindow = outcomes.stream().filter(o -> nowMs - o.timestampMs() <= windowDurationMs).toList();
            if (inWindow.isEmpty()) return false;
            long failures = inWindow.stream().filter(Outcome::failed).count();
            return (double) failures / inWindow.size() * 100 >= failureRateThreshold;
        }
    }

    public static void main(String[] args) {
        TimeBasedWindow window = new TimeBasedWindow(10_000, 50); // last 10 seconds, trip at 50%

        // a burst of 3 failures within 2 seconds, followed by a long quiet gap
        window.record(true, 0);
        window.record(true, 500);
        window.record(true, 1_500);
        System.out.println("right after burst (t=2000ms): shouldTrip=" + window.shouldTrip(2_000)); // true -- 3/3 failed

        System.out.println("10s later (t=12000ms, window has expired the burst): shouldTrip="
                + window.shouldTrip(12_000)); // false -- the failures aged out of the window entirely
    }
}
```

How to run: `java Resilience4jLevel2.java`

`TimeBasedWindow` only considers outcomes within the last `windowDurationMs` — right after the burst of failures, `shouldTrip` correctly reports `true`, but ten seconds later, those same failures have aged out of the 10-second window entirely, and `shouldTrip` reports `false` even without any new successful calls having happened — purely because time passed and the window moved forward. A count-based window with size 3 would have kept reporting `true` indefinitely, since it doesn't care how much time elapsed, only how many calls happened since.

### Level 3 — Advanced

Run two independently-configured named instances side by side — `billing-service` (count-based, tuned for its own steady traffic) and `promotions-service` (time-based, tuned for its own bursty traffic) — confirming their state is genuinely independent.

```java
import java.util.*;

public class Resilience4jLevel3 {
    static class CountBasedWindow {
        Deque<Boolean> outcomes = new ArrayDeque<>();
        int size; double threshold;
        CountBasedWindow(int size, double threshold) { this.size = size; this.threshold = threshold; }
        void record(boolean failed) { outcomes.addLast(failed); if (outcomes.size() > size) outcomes.removeFirst(); }
        boolean shouldTrip() {
            if (outcomes.size() < size) return false;
            long failures = outcomes.stream().filter(b -> b).count();
            return (double) failures / size * 100 >= threshold;
        }
    }

    static Map<String, CountBasedWindow> instances = new HashMap<>();

    static CountBasedWindow instance(String name, int size, double threshold) {
        return instances.computeIfAbsent(name, k -> new CountBasedWindow(size, threshold));
    }

    public static void main(String[] args) {
        CountBasedWindow billing = instance("billing-service", 5, 50);
        CountBasedWindow promotions = instance("promotions-service", 3, 66);

        // billing-service has a few failures, but not enough to trip its own (size 5, 50%) threshold
        for (boolean f : new boolean[]{true, false, false, false, false}) billing.record(f);
        System.out.println("billing-service shouldTrip: " + billing.shouldTrip()); // 20% -- false

        // promotions-service has heavy failures, tripping its own (size 3, 66%) threshold
        for (boolean f : new boolean[]{true, true, false}) promotions.record(f);
        System.out.println("promotions-service shouldTrip: " + promotions.shouldTrip()); // 66.6% -- true

        System.out.println("billing-service state unaffected by promotions-service: " + billing.shouldTrip()); // still false
    }
}
```

How to run: `java Resilience4jLevel3.java`

`billing-service` and `promotions-service` each get their own `CountBasedWindow`, with entirely different sizes and thresholds, tracked independently in the `instances` map. `promotions-service` tripping its own threshold has zero effect on `billing-service`'s state — the final `println` explicitly confirms `billing-service` is unchanged, exactly matching how `resilience4j.circuitbreaker.instances.billing-service.*` and `resilience4j.circuitbreaker.instances.promotions-service.*` configure genuinely separate, independent circuit breakers in a real application.

## 6. Walkthrough

Trace the sequence in Level 3.

1. `instance("billing-service", 5, 50)` and `instance("promotions-service", 3, 66)` are created via `computeIfAbsent`, each with its own configuration — `billing-service` needs a 50% failure rate over its last 5 calls to trip, while `promotions-service` needs a stricter 66% over just its last 3 calls, reflecting a deliberately different tolerance tuned for each service's own characteristics.
2. The first loop records five outcomes into `billing`: one failure, four successes. `billing.shouldTrip()` computes `1/5 = 20%`, well under its `50%` threshold, so it returns `false`.
3. The second loop records three outcomes into `promotions`: two failures, one success. `promotions.shouldTrip()` computes `2/3 ≈ 66.67%`, which is `>= 66%`, so it returns `true` — this instance's stricter, smaller window tripped based entirely on its own recorded outcomes.
4. The final `println` calls `billing.shouldTrip()` again — nothing about `promotions`'s state change affected `billing`'s own `outcomes` deque at all, since they're two completely separate objects in the `instances` map; the result is still `false`, exactly as before.

```
billing-service    (size=5, threshold=50%): [T,F,F,F,F] -> 1/5 = 20%   -> shouldTrip=false
promotions-service (size=3, threshold=66%): [T,T,F]     -> 2/3 = 66.7% -> shouldTrip=true

billing-service and promotions-service track ENTIRELY independent state -- one tripping never affects the other
```

## 7. Gotchas & takeaways

> **Gotcha:** `COUNT_BASED` windows with a small size can trip (or reset) based on a handful of calls that happen to cluster unluckily — during genuinely low-traffic periods, even 2-3 failures in a row (which might just be coincidence) can meet a small window's failure-rate threshold and trip the breaker, even though the service is mostly healthy. `TIME_BASED` windows avoid this specific issue by requiring a minimum number of calls within the actual time window (configurable via `minimum-number-of-calls`) before evaluating the failure rate at all.

- Resilience4j's sliding window is the real mechanism behind the simplified, fixed-size window used in earlier cards' examples — understanding count-based vs. time-based is the concrete configuration decision those examples were building toward.
- Each named instance (`resilience4j.circuitbreaker.instances.<name>`) is independently configured and independently tracked — there's no shared or global circuit breaker state across differently-named instances, by design.
- Choose count-based for steady, predictable traffic where "the last N calls" is a meaningful, stable sample; choose time-based for bursty or highly variable traffic where a fixed time window better reflects "recent" behavior.
- `minimum-number-of-calls` (not modeled in these simplified examples, but a real Resilience4j property) prevents a circuit breaker from making a trip decision based on too small a sample — worth setting deliberately alongside the window size and threshold.
