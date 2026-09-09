---
card: system-design
gi: 151
slug: spring-cloud-gateway-requestratelimiter-redis
title: Spring Cloud Gateway RequestRateLimiter (Redis)
---

## 1. What it is

Spring Cloud Gateway's **`RequestRateLimiter`** is a built-in gateway filter that rate-limits requests before they ever reach any downstream microservice, using Redis as the shared, distributed store for the counters. It applies a token-bucket-style algorithm (implemented as a Redis Lua script under the hood) keyed by whatever you choose — user ID, API key, or IP address — and rejects requests that exceed the configured rate with a `429` response, all at the gateway, in front of your services.

## 2. Why & when

Rate limiting inside every individual microservice means writing (or wiring) the same logic repeatedly, and a request that is going to be rejected anyway still pays the cost of being routed and processed before that rejection happens. Applying `RequestRateLimiter` at the API gateway rejects over-limit requests at the very edge of the system, before they consume any downstream capacity at all — combining the [centralized Redis counter](0147-centralized-counter-redis-rate-limiting.md) pattern with the gateway's position as the single entry point for all external traffic. Use it whenever you have a Spring Cloud Gateway (or similar API gateway) in front of multiple services and want one consistent, centrally-configured rate limit applied to all of them.

## 3. Core concept

- **`RedisRateLimiter`:** the concrete implementation backing `RequestRateLimiter`; it runs a Lua script against Redis that implements a token-bucket check atomically, avoiding the race conditions a naive multi-step check would have.
- **`replenishRate` and `burstCapacity`:** the two key configuration values — `replenishRate` is the steady tokens-per-second refill rate, and `burstCapacity` is the bucket's maximum size, directly mirroring the [token bucket](0143-token-bucket.md)'s capacity and refill rate.
- **`KeyResolver`:** a pluggable strategy deciding what the rate limit is keyed by — commonly the authenticated user's ID, an API key from a header, or the caller's IP address, letting you enforce [per-user quotas](0148-per-user-vs-global-quotas.md) at the gateway.
- **Route-level configuration:** each route in the gateway's configuration can have its own `RequestRateLimiter` filter with its own `replenishRate`/`burstCapacity`, so different APIs behind the same gateway can have different limits.
- **Response on rejection:** when the limit is hit, the gateway returns `429 Too Many Requests` directly, without forwarding the request to any downstream service, and can be configured to add [rate-limit headers](0149-rate-limit-response-headers-429-handling.md) to the response.

## 4. Diagram

```
   client
     |
     v
   +----------------------------------------------+
   | Spring Cloud Gateway                          |
   |   route: /api/orders/**                       |
   |     filter: RequestRateLimiter                |
   |       key = KeyResolver.resolve(exchange)     |
   |       redis: run token-bucket Lua script      |
   |         allowed? --- no --> 429 (stop here)   |
   |         allowed? --- yes --> forward request  |
   +----------------------------------------------+
                     |  (only allowed requests reach here)
                     v
              orders-service   (never sees a rejected request)
```
*Caption: the gateway checks the rate limit against Redis before routing anywhere — a rejected request never reaches a downstream microservice at all.*

## 5. Runnable example

This models the gateway filter's decision logic in-process; a real deployment wires the same shape through Spring Cloud Gateway's YAML configuration, shown in "How to run".

**Level 1 — Basic.** A `KeyResolver`-style function picks the rate-limit key per request.

**Level 2 — Redis-backed token bucket per key.** Reuse the token-bucket-over-Redis idea, keyed by the resolved identity, mirroring `RedisRateLimiter`.

**Level 3 — Gateway-level short-circuit.** A rejected request never reaches the "downstream service" call at all, modeling the gateway's actual behavior.

```java
// GatewayRateLimiterDemo.java
import java.util.*;
import java.util.function.*;

public class GatewayRateLimiterDemo {

    // Models one Redis-backed token bucket, keyed by resolved identity (user ID, API key, etc).
    static class RedisRateLimiter {
        final double replenishRate;   // tokens/sec, steady rate
        final long burstCapacity;     // bucket size
        final Map<String, double[]> buckets = new HashMap<>(); // [availableTokens, lastRefillMillis]

        RedisRateLimiter(double replenishRate, long burstCapacity) {
            this.replenishRate = replenishRate;
            this.burstCapacity = burstCapacity;
        }

        // Models the atomic Lua-script check-and-consume against Redis.
        boolean isAllowed(String key, long nowMillis) {
            double[] state = buckets.computeIfAbsent(key, k -> new double[]{burstCapacity, nowMillis});
            double elapsedSeconds = (nowMillis - state[1]) / 1000.0;
            state[0] = Math.min(burstCapacity, state[0] + elapsedSeconds * replenishRate);
            state[1] = nowMillis;
            if (state[0] >= 1) {
                state[0] -= 1;
                return true;
            }
            return false;
        }
    }

    // Level 1: models a Spring Cloud Gateway KeyResolver.
    static Function<String, String> apiKeyKeyResolver = requestApiKeyHeader -> "apikey:" + requestApiKeyHeader;

    // Level 3: the "downstream service" - must never be called for a rejected request.
    static String callOrdersService(String requestId) {
        return "orders-service processed " + requestId;
    }

    static void handleRequest(RedisRateLimiter limiter, String apiKeyHeader, String requestId, long nowMillis) {
        String key = apiKeyKeyResolver.apply(apiKeyHeader); // Level 1: resolve the rate-limit key
        boolean allowed = limiter.isAllowed(key, nowMillis); // Level 2: check the Redis-backed bucket
        if (!allowed) {
            System.out.println(requestId + " (key=" + key + "): 429 Too Many Requests - gateway stopped here, downstream NOT called");
            return; // Level 3: short-circuit - never reaches callOrdersService
        }
        String result = callOrdersService(requestId);
        System.out.println(requestId + " (key=" + key + "): 200 OK -> " + result);
    }

    public static void main(String[] args) {
        // replenishRate=2 tokens/sec, burstCapacity=3
        RedisRateLimiter limiter = new RedisRateLimiter(2, 3);
        long now = System.currentTimeMillis();

        // Client "key-A" sends 5 requests almost instantly - only 3 (the burst capacity) should pass.
        for (int i = 1; i <= 5; i++) {
            handleRequest(limiter, "key-A", "req-A" + i, now);
        }
        // A different client, "key-B", is completely unaffected - it has its own independent bucket.
        handleRequest(limiter, "key-B", "req-B1", now);
    }
}
```

**How to run:** save as `GatewayRateLimiterDemo.java`, then run `java GatewayRateLimiterDemo.java`. (Real Spring Cloud Gateway: configure in `application.yml` under a route's `filters`: `- name: RequestRateLimiter` with `args.redis-rate-limiter.replenishRate: 2`, `args.redis-rate-limiter.burstCapacity: 3`, plus a `KeyResolver` bean, e.g. resolving `exchange.getRequest().getHeaders().getFirst("X-API-Key")`; requires the `spring-cloud-starter-gateway` and a Redis connection.)

## 6. Walkthrough

1. Each call to `handleRequest` first resolves the rate-limit key via `apiKeyKeyResolver`, turning the raw `X-API-Key`-style header value `"key-A"` into `"apikey:key-A"` — this mirrors a real `KeyResolver` bean deciding what identity the limit applies to.
2. `req-A1` through `req-A3` each call `limiter.isAllowed`, which finds (or creates) `key-A`'s bucket starting at `burstCapacity = 3`; since almost no time passes between these calls, each one simply consumes one of the 3 starting tokens, and all three print `200 OK`.
3. `req-A4` finds `state[0]` already near 0 (the tiny elapsed time added a negligible refill), so `state[0] >= 1` is false, `isAllowed` returns `false`, and `handleRequest` prints the `429` line and returns immediately — critically, `callOrdersService` is never invoked for this request, exactly modeling the gateway's short-circuit behavior.
4. `req-A5` is rejected the same way, for the same reason.
5. `req-B1` uses a completely different resolved key, `"apikey:key-B"`; `buckets.computeIfAbsent` creates a brand-new bucket for it, starting fresh at `burstCapacity = 3`, so it is allowed and reaches `callOrdersService` — confirming that `key-A`'s exhausted bucket has no effect on any other client's own independent limit.

## 7. Gotchas & takeaways

> Gotcha: forgetting to configure a custom `KeyResolver` leaves Spring Cloud Gateway's default resolver in place, which is often "no key" (a single global bucket for all traffic) — this silently turns what you intended as a per-user limit into a [global quota](0148-per-user-vs-global-quotas.md) shared by every caller, so always verify which `KeyResolver` bean is actually active for your routes.

- Rate limiting at the gateway rejects over-limit requests at the very edge of the system, before any downstream service does any work for them.
- `replenishRate` and `burstCapacity` are the same token-bucket parameters covered earlier, just configured declaratively per gateway route.
- The `KeyResolver` is the piece that decides whether you are enforcing a per-user limit, a per-API-key limit, or (by misconfiguration) an accidental global one.
- Related concepts: [Token bucket](0143-token-bucket.md) (the algorithm this filter implements), [Centralized counter (Redis) rate limiting](0147-centralized-counter-redis-rate-limiting.md) (the same Redis-backed correctness pattern), [Bucket4j for token-bucket rate limiting](0150-bucket4j-for-token-bucket-rate-limiting.md) (the same algorithm, applied inside a single service instead of at the gateway).
