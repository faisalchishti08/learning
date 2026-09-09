---
card: system-design
gi: 143
slug: token-bucket
title: Token bucket
---

## 1. What it is

The **token bucket** algorithm limits how many requests a client can make by giving it a bucket that holds a fixed number of tokens. Each request must remove one token from the bucket to proceed; if the bucket is empty, the request is rejected or delayed. Tokens refill at a steady rate, up to the bucket's maximum size. Think of it like a subway turnstile that only lets people through if they have a token, and a machine slowly drops fresh tokens into a tray all day.

## 2. Why & when

A service must stop any single client from sending so many requests that it starves other clients or overloads a downstream dependency. A naive counter that resets every second either blocks all traffic instantly once the count is hit, or allows a sudden burst right at the boundary between two windows. The token bucket fixes both problems: it allows short bursts up to the bucket size, while still enforcing a steady average rate over time. Use it for API rate limiting, controlling outbound calls to a third-party API with a strict quota, or shaping network traffic.

## 3. Core concept

- **Bucket capacity:** the maximum number of tokens the bucket can hold, which is also the largest burst a client can send instantly.
- **Refill rate:** tokens are added at a fixed rate (e.g. 10 tokens per second), modeling the sustained average rate you want to allow.
- **Consume on request:** each incoming request tries to remove one (or more, for a weighted request) token; if enough tokens exist, the request proceeds and the tokens are removed; otherwise the request is rejected or queued.
- **Lazy refill:** most real implementations do not run a background timer. Instead, on each request they compute how much time passed since the last check, and add `elapsed_time * refill_rate` tokens, capped at the bucket capacity.
- **Bursts, bounded by capacity:** because tokens accumulate while idle, a client that has not made requests for a while can burst up to the full bucket capacity, then must slow to the refill rate.

## 4. Diagram

```
   refill rate: 2 tokens/sec              capacity: 5 tokens
        |                                        |
        v                                        v
   +---------------------------------------------+
   |  ***  ***  ***  ***  ***                    |   <- tokens (max 5)
   +---------------------------------------------+
                     |
              request arrives
                     |
              enough tokens? --- yes --> remove 1 token, request proceeds
                     |
                     no --> request rejected (429) or queued
```
*Caption: tokens drip in at a steady rate; a request only proceeds if it can take a token out, and the bucket never overflows past its capacity.*

## 5. Runnable example

**Level 1 — Basic.** A bucket with a fixed capacity and refill rate, consuming one token per request.

**Level 2 — Lazy refill by elapsed time.** Compute tokens to add based on real elapsed time instead of a background thread.

**Level 3 — Weighted requests.** Allow a request to cost more than one token, for operations that are more expensive to serve.

```java
// TokenBucketDemo.java
public class TokenBucketDemo {

    static class TokenBucket {
        final long capacity;
        final double refillTokensPerSecond;
        double availableTokens;
        long lastRefillTimeNanos;

        TokenBucket(long capacity, double refillTokensPerSecond) {
            this.capacity = capacity;
            this.refillTokensPerSecond = refillTokensPerSecond;
            this.availableTokens = capacity; // start full
            this.lastRefillTimeNanos = System.nanoTime();
        }

        // Level 2: lazily refill based on elapsed time since the last check.
        private void refill() {
            long now = System.nanoTime();
            double elapsedSeconds = (now - lastRefillTimeNanos) / 1_000_000_000.0;
            double tokensToAdd = elapsedSeconds * refillTokensPerSecond;
            availableTokens = Math.min(capacity, availableTokens + tokensToAdd);
            lastRefillTimeNanos = now;
        }

        // Level 3: allow a request to consume more than one token.
        boolean tryConsume(int tokensRequested) {
            refill();
            if (availableTokens >= tokensRequested) {
                availableTokens -= tokensRequested;
                return true;
            }
            return false;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        // capacity 5, refills 2 tokens/sec
        TokenBucket bucket = new TokenBucket(5, 2.0);

        // Level 1: burst of 5 cheap requests drains the full bucket instantly.
        for (int i = 1; i <= 6; i++) {
            boolean allowed = bucket.tryConsume(1);
            System.out.println("request " + i + " (cost 1): " + (allowed ? "ALLOWED" : "REJECTED (429)"));
        }

        System.out.println("waiting 1 second for refill...");
        Thread.sleep(1000);

        // Level 3: a weighted request costing 2 tokens after partial refill.
        boolean allowedHeavy = bucket.tryConsume(2);
        System.out.println("heavy request (cost 2) after refill: " + (allowedHeavy ? "ALLOWED" : "REJECTED (429)"));
    }
}
```

**How to run:** save as `TokenBucketDemo.java`, then run `java TokenBucketDemo.java`.

## 6. Walkthrough

1. The bucket starts full, with `availableTokens = 5` (its `capacity`).
2. Requests 1 through 5 each call `tryConsume(1)`; `refill()` adds almost no tokens since almost no time has passed, so each request removes 1 token and `availableTokens` drops from 5 to 0.
3. Request 6 arrives with `availableTokens` at 0; `tryConsume` finds `availableTokens < tokensRequested` and returns `false`, so the demo prints "REJECTED (429)".
4. After sleeping 1 second, the next call to `refill()` computes `elapsedSeconds ≈ 1.0` and `tokensToAdd = 1.0 * 2.0 = 2.0`, raising `availableTokens` to 2 (capped at `capacity`, which does not bind here).
5. The heavy request asks for 2 tokens with `tryConsume(2)`; since `availableTokens` is now 2, the check passes, both tokens are removed, and the request is allowed — demonstrating that a weighted request is rejected unless enough accumulated tokens cover its full cost.

## 7. Gotchas & takeaways

> Gotcha: computing the refill using floating-point elapsed time on every request, without ever capping at `capacity`, lets tiny timing inconsistencies (a very long gap between requests) hand out far more tokens than the bucket was designed to hold — always clamp `availableTokens` to `capacity` after adding the refill, exactly as `Math.min(capacity, ...)` does here.

- The token bucket allows a burst up to the bucket's capacity, then throttles down to the steady refill rate — this is its key advantage over a hard fixed-window counter.
- Lazy refill (computing elapsed time on each request) avoids running a background thread just to add tokens, and scales to many independent buckets (e.g. one per user) cheaply.
- Weighting requests by token cost lets you rate-limit by real resource cost, not just request count.
- Related concepts: [Leaky bucket](0144-leaky-bucket.md) (a stricter alternative that smooths output instead of allowing bursts), [Bucket4j for token-bucket rate limiting](0150-bucket4j-for-token-bucket-rate-limiting.md) (a production Java library implementing this exact algorithm), [Rate-limit response headers & 429 handling](0149-rate-limit-response-headers-429-handling.md) (what a rejected request should tell the caller).
