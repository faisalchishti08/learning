---
card: microservices
gi: 274
slug: token-bucket-algorithm
title: "Token bucket algorithm"
---

## 1. What it is

The token bucket algorithm implements [rate limiting](0273-rate-limiter-pattern.md) using an imaginary bucket that holds a limited number of tokens: each request consumes one token, tokens are added back to the bucket at a steady rate up to the bucket's capacity, and a request is only permitted if a token is currently available — allowing short bursts (spending accumulated, saved-up tokens all at once) while still enforcing a long-term average rate.

## 2. Why & when

A naive rate limiter that rigidly enforces exactly N requests every fixed interval, with no flexibility, can be needlessly restrictive for traffic that's naturally bursty but still averages out to an acceptable rate over time — a client that's been quiet for a while and then needs to send a quick burst of requests shouldn't necessarily be penalized identically to a client sending a perfectly steady stream, if the overall average rate both clients produce is the same. The token bucket algorithm's design directly supports this: tokens accumulate during quiet periods (up to the bucket's capacity), so a burst can be absorbed by spending those saved-up tokens, while the steady refill rate ensures the long-term average throughput still stays bounded — a deliberate, tunable compromise between rigid, no-burst-tolerance rate limiting and unbounded burst tolerance.

Use token bucket when some burst tolerance is desirable — allowing clients to "save up" capacity during quiet periods and spend it during a legitimate burst — while still enforcing a long-term average rate limit. This is the algorithm behind many popular rate-limiting implementations (including many API gateways and cloud provider rate limits) precisely because this burst tolerance matches real-world traffic patterns well.

## 3. Core concept

The bucket starts with (or refills toward) a maximum token capacity, refilling at a fixed rate over time (either continuously or in discrete steps); each request checks whether at least one token is available, consuming it if so and rejecting the request if the bucket is empty — the bucket's capacity determines the maximum burst size, and the refill rate determines the long-term sustained rate.

```java
class TokenBucket {
    double tokens; // CURRENT token count, can be fractional between refills
    final double capacity; // MAXIMUM tokens the bucket can hold -- the BURST size limit
    final double refillRatePerSecond; // tokens added PER SECOND -- the SUSTAINED rate limit
    long lastRefillTimeMillis;

    boolean tryConsume() {
        refill(); // top up based on ELAPSED time since the last check
        if (tokens >= 1) { tokens -= 1; return true; } // a TOKEN available -- request PERMITTED
        return false; // BUCKET EMPTY -- request REJECTED
    }

    void refill() {
        long now = System.currentTimeMillis();
        double elapsedSeconds = (now - lastRefillTimeMillis) / 1000.0;
        tokens = Math.min(capacity, tokens + elapsedSeconds * refillRatePerSecond); // ADD tokens, CAPPED at capacity
        lastRefillTimeMillis = now;
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bucket holds accumulated tokens up to a maximum capacity; tokens refill steadily over time up to that cap, each request consumes one token if available, and a burst of requests can be absorbed by spending accumulated tokens all at once, while the steady refill rate governs the long-term sustained throughput" >
  <rect x="40" y="20" width="100" height="130" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="50" y="70" width="80" height="70" fill="#6db33f" opacity="0.3"/>
  <text x="90" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">tokens</text>
  <text x="90" y="165" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">bucket (capacity-bounded)</text>

  <text x="240" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">steady REFILL rate</text>
  <line x1="180" y1="70" x2="240" y2="70" stroke="#8b949e" marker-end="url(#arr274)"/>

  <rect x="320" y="65" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="385" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">request consumes 1</text>
  <line x1="140" y1="105" x2="318" y2="85" stroke="#8b949e" marker-end="url(#arr274)"/>

  <text x="530" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">burst = spend saved tokens</text>

  <defs>
    <marker id="arr274" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Accumulated tokens absorb bursts; the refill rate bounds the average, sustained throughput over time.

## 5. Runnable example

Scenario: a token bucket started empty, showing requests correctly rejected until tokens accumulate, extended to demonstrate accumulated tokens absorbing a legitimate burst that a rigid fixed-rate limiter would have rejected, and finally showing the long-term average rate still correctly bounded even after a burst, confirming the algorithm's dual burst-tolerance-and-average-limiting behavior.

### Level 1 — Basic

```java
// File: EmptyBucketRejectsUntilRefilled.java -- a bucket STARTING empty
// rejects requests until tokens have had time to ACCUMULATE via refill.
public class EmptyBucketRejectsUntilRefilled {
    static class TokenBucket {
        double tokens = 0; // STARTS empty
        final double capacity = 10;
        final double refillRatePerSecond = 5; // 5 tokens/second
        long lastRefillTimeMillis = System.currentTimeMillis();

        boolean tryConsume() {
            refill();
            if (tokens >= 1) { tokens -= 1; return true; }
            return false;
        }
        void refill() {
            long now = System.currentTimeMillis();
            double elapsedSeconds = (now - lastRefillTimeMillis) / 1000.0;
            tokens = Math.min(capacity, tokens + elapsedSeconds * refillRatePerSecond);
            lastRefillTimeMillis = now;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        TokenBucket bucket = new TokenBucket();
        System.out.println("Immediate request on an EMPTY bucket: " + (bucket.tryConsume() ? "ALLOWED" : "REJECTED (no tokens yet)"));

        Thread.sleep(400); // wait ~0.4s -- refills ~2 tokens (5/sec * 0.4s)
        System.out.println("After 400ms of refill: " + (bucket.tryConsume() ? "ALLOWED (a token accumulated)" : "REJECTED"));
    }
}
```

**How to run:** `javac EmptyBucketRejectsUntilRefilled.java && java EmptyBucketRejectsUntilRefilled` (JDK 17+).

Expected output:
```
Immediate request on an EMPTY bucket: REJECTED (no tokens yet)
After 400ms of refill: ALLOWED (a token accumulated)
```

### Level 2 — Intermediate

```java
// File: AccumulatedTokensAbsorbBurst.java -- LETTING the bucket sit idle
// (accumulating tokens up to capacity) means a SUBSEQUENT burst is
// ABSORBED cleanly -- a RIGID fixed-rate limiter would have rejected most of it.
public class AccumulatedTokensAbsorbBurst {
    static class TokenBucket {
        double tokens;
        final double capacity;
        final double refillRatePerSecond;
        long lastRefillTimeMillis = System.currentTimeMillis();

        TokenBucket(double capacity, double refillRatePerSecond) {
            this.capacity = capacity; this.tokens = capacity; this.refillRatePerSecond = refillRatePerSecond; // starts FULL, for this demo
        }
        boolean tryConsume() {
            refill();
            if (tokens >= 1) { tokens -= 1; return true; }
            return false;
        }
        void refill() {
            long now = System.currentTimeMillis();
            double elapsedSeconds = (now - lastRefillTimeMillis) / 1000.0;
            tokens = Math.min(capacity, tokens + elapsedSeconds * refillRatePerSecond);
            lastRefillTimeMillis = now;
        }
    }

    public static void main(String[] args) {
        TokenBucket bucket = new TokenBucket(10, 2); // capacity=10 (a full "saved up" allowance), refill=2/sec (a MODEST sustained rate)

        int allowed = 0, rejected = 0;
        for (int i = 0; i < 15; i++) { // a BURST of 15 requests, essentially instantly
            if (bucket.tryConsume()) allowed++; else rejected++;
        }
        System.out.println("Burst of 15 requests against a bucket that had accumulated to FULL capacity (10):");
        System.out.println("Allowed: " + allowed + " (the FULL accumulated capacity, spent all at once)");
        System.out.println("Rejected: " + rejected + " (beyond what even the SAVED capacity could cover)");
    }
}
```

**How to run:** `javac AccumulatedTokensAbsorbBurst.java && java AccumulatedTokensAbsorbBurst` (JDK 17+).

Expected output:
```
Burst of 15 requests against a bucket that had accumulated to FULL capacity (10):
Allowed: 10 (the FULL accumulated capacity, spent all at once)
Rejected: 5 (beyond what even the SAVED capacity could cover)
```

### Level 3 — Advanced

```java
// File: LongTermAverageStillBounded.java -- even AFTER a burst spends
// down the bucket, the SUSTAINED, LONG-TERM average rate is STILL
// correctly bounded by the refill rate -- confirming the DUAL guarantee.
public class LongTermAverageStillBounded {
    static class TokenBucket {
        double tokens;
        final double capacity;
        final double refillRatePerSecond;
        long lastRefillTimeMillis = System.currentTimeMillis();

        TokenBucket(double capacity, double refillRatePerSecond) {
            this.capacity = capacity; this.tokens = capacity; this.refillRatePerSecond = refillRatePerSecond;
        }
        boolean tryConsume() {
            refill();
            if (tokens >= 1) { tokens -= 1; return true; }
            return false;
        }
        void refill() {
            long now = System.currentTimeMillis();
            double elapsedSeconds = (now - lastRefillTimeMillis) / 1000.0;
            tokens = Math.min(capacity, tokens + elapsedSeconds * refillRatePerSecond);
            lastRefillTimeMillis = now;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        TokenBucket bucket = new TokenBucket(10, 5); // capacity=10, refill=5/sec

        // STEP 1: spend the bucket DOWN to empty via an initial burst
        int burstAllowed = 0;
        for (int i = 0; i < 10; i++) if (bucket.tryConsume()) burstAllowed++;
        System.out.println("Initial burst spent " + burstAllowed + " tokens -- bucket now near empty.");

        // STEP 2: measure the SUSTAINED rate over the NEXT 2 seconds -- should be bounded near refillRatePerSecond
        int sustainedAllowed = 0;
        long testStart = System.currentTimeMillis();
        while (System.currentTimeMillis() - testStart < 2000) {
            if (bucket.tryConsume()) sustainedAllowed++;
            Thread.sleep(10); // poll frequently, simulating a steady stream of attempted requests
        }
        System.out.println("Requests allowed over the NEXT 2 seconds (bucket already drained): " + sustainedAllowed);
        System.out.println("Expected sustained rate: ~" + (5 * 2) + " (refillRatePerSecond * 2 seconds) -- the algorithm correctly bounds the LONG-TERM average, even right after a burst.");
    }
}
```

**How to run:** `javac LongTermAverageStillBounded.java && java LongTermAverageStillBounded` (JDK 17+).

Expected output (approximate, timing-dependent):
```
Initial burst spent 10 tokens -- bucket now near empty.
Requests allowed over the NEXT 2 seconds (bucket already drained): 10
Expected sustained rate: ~10 (refillRatePerSecond * 2 seconds) -- the algorithm correctly bounds the LONG-TERM average, even right after a burst.
```

## 6. Walkthrough

1. **Level 1, an empty bucket correctly rejecting** — `TokenBucket` starts with `tokens = 0`; the first `tryConsume()` call runs `refill()` (which adds essentially zero tokens, since almost no time has elapsed since `lastRefillTimeMillis` was just set), finds `tokens < 1`, and correctly returns `false`.
2. **Level 1, refill accumulating over real elapsed time** — after `Thread.sleep(400)`, the next `tryConsume()` call's `refill()` computes `elapsedSeconds ≈ 0.4` and adds `0.4 × 5 = 2` tokens (capped at `capacity`, though far from it here), bringing `tokens` above 1 and allowing the request — demonstrating the refill mechanism working correctly based on genuine elapsed wall-clock time.
3. **Level 2, a bucket allowed to accumulate to full capacity** — this `TokenBucket` is constructed with `tokens = capacity` directly (10), modeling a bucket that's been idle long enough to fully refill; a burst of 15 rapid, essentially simultaneous `tryConsume()` calls immediately follows, with no meaningful time passing between them for further refill to occur.
4. **Level 2, the burst partially absorbed** — the first 10 of the 15 requests succeed, consuming the bucket's full accumulated capacity one token at a time, while the remaining 5 fail once the bucket is empty — this demonstrates the burst-tolerance the token bucket provides: a client that had been quiet (letting tokens accumulate) can legitimately spend that entire saved allowance in a rapid burst, something a rigid, no-accumulation rate limiter would never permit.
5. **Level 3, draining the bucket and then measuring sustained throughput** — the initial loop of 10 `tryConsume()` calls (against a bucket starting full at capacity 10) drains it to near-zero almost immediately, mirroring Level 2's burst-absorption behavior; the subsequent 2-second measurement loop then repeatedly attempts `tryConsume()` while the bucket has essentially no accumulated buffer left to draw on.
6. **Level 3, the long-term rate correctly bounded** — with `refillRatePerSecond = 5`, over a 2-second measurement window the bucket can refill and therefore permit roughly `5 × 2 = 10` additional requests, and the measured `sustainedAllowed` count comes out close to this expected value — confirming that even immediately following a burst that fully drained the accumulated buffer, the algorithm's *sustained* throughput correctly settles to the configured refill rate, exactly the dual guarantee the token bucket algorithm is designed to provide: generous short-term burst tolerance from accumulated capacity, combined with a strictly bounded long-term average rate once that accumulated buffer is exhausted.

## 7. Gotchas & takeaways

> **Gotcha:** the bucket's `capacity` parameter controls the *maximum burst size*, and the `refillRatePerSecond` controls the *sustained average rate* — these are two genuinely independent tunables, and conflating them (assuming a larger capacity alone increases the sustained rate, or that a faster refill rate alone increases burst tolerance) leads to misconfiguring one dimension while trying to tune the other; adjust capacity specifically to change how large a legitimate burst can be absorbed, and adjust the refill rate specifically to change the long-term sustained throughput ceiling.

- The token bucket algorithm permits a request if a token is available in the bucket, consumes one token per request, and refills tokens steadily over time up to the bucket's maximum capacity.
- Bucket capacity determines the maximum burst size a client can spend at once (from accumulated, saved-up tokens); refill rate determines the long-term sustained average throughput.
- This provides a deliberate compromise between rigid, no-burst-tolerance rate limiting and unbounded bursting — bursts are tolerated up to the accumulated capacity, while the average rate over time remains strictly bounded by the refill rate.
- A bucket that's been idle (accumulating tokens toward its capacity) can absorb a legitimate burst that a stricter, non-accumulating rate limiter would reject outright.
- Bucket capacity and refill rate are independent tunables addressing different concerns — burst size versus sustained rate — and should be adjusted deliberately and separately based on which specific behavior needs changing.
