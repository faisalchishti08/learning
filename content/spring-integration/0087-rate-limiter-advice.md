---
card: spring-integration
gi: 87
slug: rate-limiter-advice
title: "Rate limiter advice"
---

## 1. What it is

Rate limiter advice wraps a message handler to cap how many messages it processes within a given time window, commonly implemented via a custom `MethodInterceptor`-based advice or by wiring in a dedicated rate-limiting library (like Resilience4j's `RateLimiter`, which pairs naturally with Spring Integration's advice mechanism). Where retry advice and circuit-breaker advice (card 0086) react to failures, rate limiter advice proactively caps throughput regardless of whether calls are succeeding, protecting a downstream dependency (or an externally imposed quota) from ever being sent more traffic than it's allowed to receive.

## 2. Why & when

You reach for rate limiter advice when the concern is volume itself, not failure:

- **A downstream API enforces a rate limit and exceeding it causes errors or throttling** — many third-party APIs (payment processors, external data providers) reject or penalize requests beyond a contracted rate; a rate limiter advice on the outbound call keeps the flow within that budget proactively, rather than reactively handling 429 responses after the fact.
- **A shared internal resource has finite capacity regardless of whether individual calls are failing** — a downstream service might be handling requests successfully but degrade under too much concurrent volume; capping request rate protects it before it starts failing, rather than only reacting once it does (which is what circuit-breaker advice does).
- **Fairness across multiple message producers matters** — if several sources feed into the same handler and the downstream capacity must be shared, a rate limiter enforces an overall ceiling regardless of which source happens to be busiest at a given moment.

## 3. Core concept

Think of a circuit breaker as a smoke detector — it reacts once something is already going wrong. A rate limiter is more like a turnstile at a venue with a fixed capacity: it doesn't wait for the venue to become overcrowded and unsafe before acting — it simply admits people at a steady, pre-agreed rate from the start, so the venue never gets more crowded than its capacity allows in the first place. The two mechanisms are complementary: the turnstile prevents the crowding that might otherwise trigger the smoke detector's underlying cause.

```java
@Bean
public IntegrationFlow rateLimitedApiFlow() {
    return IntegrationFlow.from("apiCallRequests")
        .handle(externalApiClient::call, e -> e.advice(rateLimiterAdvice()))
        .get();
}

@Bean
public RateLimiterRequestHandlerAdvice rateLimiterAdvice() {
    RateLimiterConfig config = RateLimiterConfig.custom()
        .limitForPeriod(10)                       // 10 calls
        .limitRefreshPeriod(Duration.ofSeconds(1)) // per second
        .timeoutDuration(Duration.ofMillis(500))   // wait up to 500ms for a permit before failing
        .build();
    return new RateLimiterRequestHandlerAdvice(RateLimiter.of("externalApi", config));
}
```

At most 10 calls per second reach `externalApiClient`, regardless of how many messages arrive on `apiCallRequests` in that window — excess messages wait briefly for a permit, or fail if none becomes available within the timeout.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A rate limiter admits calls at a steady configured rate regardless of arrival bursts, holding excess calls briefly or rejecting them if no permit becomes available in time" >
  <rect x="20" y="20" width="600" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="35" y="42" fill="#e6edf3" font-size="8" font-family="monospace">Arrivals: msg msg msg msg msg msg msg msg msg msg msg msg (burst of 12 in one instant)</text>

  <rect x="20" y="75" width="500" height="35" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="35" y="97" fill="#79c0ff" font-size="8" font-family="monospace">Admitted: 10 per second, evenly paced -- excess wait for the next window</text>

  <text x="320" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">The downstream call rate stays capped even when arrivals spike well above it</text>
</svg>

The limiter smooths a bursty arrival pattern into a steady, capped rate of actual downstream calls.

## 5. Runnable example

The scenario: capping calls to an external API at a fixed rate per time window, simulated with a plain token-bucket-style counter standing in for a Resilience4j `RateLimiter` (no real rate-limiting library needed to demonstrate the admit-or-wait/reject logic), starting with a basic fixed-window cap, then adding a timeout for calls that can't get a permit quickly enough, then adding per-source fairness so one busy producer can't starve another sharing the same limiter.

### Level 1 — Basic

```java
// RateLimiterDemo.java
import java.util.*;

public class RateLimiterDemo {
    // Stand-in for a RateLimiter configured with limitForPeriod(3) per window.
    static class SimpleRateLimiter {
        private final int limitPerWindow;
        private int usedThisWindow = 0;

        SimpleRateLimiter(int limitPerWindow) { this.limitPerWindow = limitPerWindow; }

        boolean tryAcquire() {
            if (usedThisWindow < limitPerWindow) {
                usedThisWindow++;
                return true;
            }
            return false;
        }

        void resetWindow() { usedThisWindow = 0; }
    }

    public static void main(String[] args) {
        SimpleRateLimiter limiter = new SimpleRateLimiter(3);
        for (int i = 1; i <= 5; i++) {
            if (limiter.tryAcquire()) {
                System.out.println("Call " + i + ": permit acquired, calling API");
            } else {
                System.out.println("Call " + i + ": no permit available, rejected");
            }
        }
    }
}
```

How to run: `java RateLimiterDemo.java`. Expected output: calls 1-3 acquire a permit and proceed; calls 4-5 are rejected — the fixed per-window cap enforced regardless of how many calls actually arrived.

### Level 2 — Intermediate

```java
// RateLimiterDemo.java
import java.util.*;
import java.util.concurrent.*;

public class RateLimiterDemo {
    static class SimpleRateLimiter {
        private final int limitPerWindow;
        private int usedThisWindow = 0;
        SimpleRateLimiter(int limitPerWindow) { this.limitPerWindow = limitPerWindow; }
        synchronized boolean tryAcquire() {
            if (usedThisWindow < limitPerWindow) { usedThisWindow++; return true; }
            return false;
        }
        synchronized void resetWindow() { usedThisWindow = 0; }
    }

    // Real-world concern: instead of rejecting immediately when no permit is available, wait
    // briefly (up to a timeout) for the next window to open -- absorbing small bursts smoothly
    // rather than rejecting every call that arrives even microseconds too early.
    static boolean acquireWithTimeout(SimpleRateLimiter limiter, long timeoutMillis) throws InterruptedException {
        long deadline = System.currentTimeMillis() + timeoutMillis;
        while (System.currentTimeMillis() < deadline) {
            if (limiter.tryAcquire()) return true;
            Thread.sleep(20);
        }
        return false;
    }

    public static void main(String[] args) throws InterruptedException {
        SimpleRateLimiter limiter = new SimpleRateLimiter(2);

        Timer windowResetter = new Timer(true);
        windowResetter.scheduleAtFixedRate(new TimerTask() {
            public void run() { limiter.resetWindow(); }
        }, 100, 100); // window resets every 100ms in this simulation

        for (int i = 1; i <= 4; i++) {
            boolean acquired = acquireWithTimeout(limiter, 150);
            System.out.println("Call " + i + ": " + (acquired ? "permit acquired" : "timed out waiting"));
        }
        windowResetter.cancel();
    }
}
```

How to run: `java RateLimiterDemo.java`. Expected output: calls that exceed the immediate per-window limit wait (rather than rejecting outright) and typically succeed once the next window resets within the 150ms timeout — demonstrating graceful absorption of a small burst instead of rejecting every call that narrowly misses the current window.

### Level 3 — Advanced

```java
// RateLimiterDemo.java
import java.util.*;
import java.util.concurrent.*;

public class RateLimiterDemo {
    static class SimpleRateLimiter {
        private final int limitPerWindow;
        private int usedThisWindow = 0;
        SimpleRateLimiter(int limitPerWindow) { this.limitPerWindow = limitPerWindow; }
        synchronized boolean tryAcquire() {
            if (usedThisWindow < limitPerWindow) { usedThisWindow++; return true; }
            return false;
        }
        synchronized void resetWindow() { usedThisWindow = 0; }
    }

    // Production concern: several producers share ONE downstream rate limit. Without fairness,
    // a busy producer can grab every available permit before a quieter producer ever gets a
    // chance -- round-robin admission across sources keeps one source from starving another.
    static class FairSharedRateLimiter {
        private final SimpleRateLimiter underlying;
        private final Queue<String> pendingSources = new LinkedList<>();

        FairSharedRateLimiter(int limitPerWindow) { this.underlying = new SimpleRateLimiter(limitPerWindow); }

        void enqueue(String source) { pendingSources.add(source); }

        void resetWindow() { underlying.resetWindow(); }

        void processQueueRoundRobin() {
            int processedThisRound = 0;
            int queueSizeAtStart = pendingSources.size();
            while (processedThisRound < queueSizeAtStart && underlying.tryAcquire()) {
                String source = pendingSources.poll();
                System.out.println("Admitted call from " + source);
                processedThisRound++;
            }
            System.out.println("Remaining queued (waiting for next window): " + pendingSources.size());
        }
    }

    public static void main(String[] args) {
        FairSharedRateLimiter limiter = new FairSharedRateLimiter(3);

        // producer-A is busy and enqueues many calls; producer-B enqueues just one.
        for (int i = 0; i < 4; i++) limiter.enqueue("producer-A");
        limiter.enqueue("producer-B");

        limiter.processQueueRoundRobin();
    }
}
```

How to run: `java RateLimiterDemo.java`. Expected output: three "Admitted call from producer-A" lines (the queue is FIFO in this simplified model, so `producer-B`'s single call waits behind `producer-A`'s first three), then `Remaining queued (waiting for next window): 2` — showing that without genuine round-robin fairness (rather than plain FIFO), a busy producer can still dominate the available permits; a production-grade fair limiter would interleave sources rather than draining one queue fully before considering another, a refinement worth calling out explicitly when fairness genuinely matters.

## 6. Walkthrough

Trace a burst of API calls through rate-limiting admission control.

1. **Messages arrive**: a burst of requests needing an external API call arrives on the flow's input channel, potentially far more in a short window than the API's contracted rate allows.
2. **Permit request**: each message's `.handle(...)` step, wrapped with rate limiter advice, requests a permit from the shared rate limiter before the actual API call is made.
3. **Permit available**: if the current window still has capacity, the permit is granted immediately and the call proceeds normally, counting against that window's budget.
4. **Permit unavailable, within timeout**: if the current window is exhausted but the configured timeout hasn't elapsed, the request waits, checking again as the window resets — absorbing brief bursts smoothly rather than rejecting them outright.
5. **Permit unavailable, timeout exceeded**: if no permit becomes available within the configured wait time, the call is rejected (typically raising an exception the flow can route to a fallback or an error channel), rather than waiting indefinitely and blocking the message indefinitely.
6. **Window reset**: after the configured period elapses, the rate limiter's budget resets, and pending or new requests can again acquire permits — the cycle repeats continuously as long as the flow is running.

```
burst of messages arrives
  -> each requests a permit from the shared rate limiter
       permit available          -> call proceeds
       unavailable, within wait  -> wait, retry as window resets
       unavailable, timeout hit  -> reject / route to fallback
  -> window resets periodically, freeing new permits
```

## 7. Gotchas & takeaways

> **Gotcha:** a rate limiter shared across multiple producers without any fairness mechanism can let one high-volume source consume the entire budget before a lower-volume source ever gets a permit — if fairness across sources genuinely matters, the limiter needs explicit round-robin or per-source sub-quotas, not just a single shared counter that whoever asks first exhausts.

- Rate limiting is proactive (cap volume before problems occur); circuit breaking (card 0086) is reactive (respond after failures accumulate) — the two address different failure modes and are often used together, not as substitutes for each other.
- Always define explicit behavior for a request that can't get a permit in time — silently dropping it, queuing it indefinitely, and failing it outright are all valid choices depending on the use case, but the choice needs to be deliberate rather than whatever the default happens to be.
- Match the rate limiter's configured rate to the actual contracted or safe limit of the downstream dependency — setting it too generously defeats its purpose, and setting it too conservatively throttles legitimate traffic the downstream system could actually handle.
- When several message sources share one rate-limited resource, consider whether fairness across sources matters for the use case; if it does, a plain shared counter isn't enough on its own.
