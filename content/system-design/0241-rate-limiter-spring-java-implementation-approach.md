---
card: system-design
gi: 241
slug: rate-limiter-spring-java-implementation-approach
title: Rate Limiter — Spring/Java implementation approach
---

## 1. What it is

This page covers the **Spring/Java implementation approach** facet of the **Rate Limiter** case study — how the [token-bucket algorithm](0239-rate-limiter-deep-dive-distributed-counter-accuracy-algorith.md), the [shared-store architecture](0237-rate-limiter-high-level-architecture.md), and the [API contract](0236-rate-limiter-api-design.md) become a real Spring Boot component: a filter or interceptor that gates every request.

## 2. Why & when

Every earlier facet described the design; this facet shows it as working code — the natural closing point of a system-design walkthrough, and the piece that would actually run in front of a real Spring Boot service.

## 3. Core concept

- **`RateLimitFilter` — a `jakarta.servlet.Filter` (or a Spring `HandlerInterceptor`).** Runs before the request reaches any `@RestController`, which is exactly where the [API design](0236-rate-limiter-api-design.md) placed the `allow(...)` check — as early in the request lifecycle as possible, so a rejected request never runs any real business logic.
- **`RateLimiterService` — a `@Service` implementing `allow(clientId, ruleName)`.** Holds the token-bucket logic from the [deep-dive facet](0239-rate-limiter-deep-dive-distributed-counter-accuracy-algorith.md), backed by a `RedisTemplate` (or similar) for the shared store from [high-level architecture](0237-rate-limiter-high-level-architecture.md) in a real deployment — this demo uses an in-memory stand-in, annotated to show where the real Redis calls would go.
- **`RateLimitConfig` — a `@ConfigurationProperties`-bound bean** holding the per-tier rules from [data model & schema](0238-rate-limiter-data-model-schema.md), loaded from `application.yml`, satisfying FR-4 without hardcoding limits in Java code.
- **Response headers added via the filter, not the controller.** Because the filter runs for every request regardless of which controller handles it, adding `X-RateLimit-*` headers there (rather than in each controller) guarantees FR-5 is satisfied uniformly across every endpoint, with zero per-endpoint code.
- **Fail-open handled at the filter's exception boundary.** A `try/catch` around the store call inside the filter, defaulting to allowing the request through on any store failure, directly implements NFR-5.

## 4. Diagram

```
   Incoming request
        |
        v
  +----------------------------+
  |     RateLimitFilter          |   implements jakarta.servlet.Filter
  |  - resolve clientId           |   - runs BEFORE any @RestController
  |  - call RateLimiterService     |
  |  - on allow=false: 429, stop    |
  |  - on allow=true: add headers,   |
  |    continue to controller          |
  +-------------+--------------+
                |
                v
  +----------------------------+
  |    RateLimiterService         |   @Service
  |  - token bucket algorithm      |   - reads RateLimitConfig for limits
  |  - (real deployment: backed      |
  |     by Redis via RedisTemplate)   |
  +----------------------------+
                |
                v
        (request proceeds to)
  +----------------------------+
  |      @RestController          |   business logic, unaware of rate
  |     (e.g. OrderController)     |   limiting entirely
  +----------------------------+
```
*Caption: the filter is a hard gate before any controller runs — controllers themselves need zero rate-limiting code, since the concern is fully centralized in the filter and service layer.*

## 5. Runnable example

**Level 1 — Basic.** A `RateLimiterService` (token bucket) and a `RateLimitFilter`-equivalent gating a simulated request.

**Level 2 — Intermediate.** Per-tier configuration (FR-4) driving different limits for different simulated clients.

**Level 3 — Advanced.** The filter adding response headers on success, returning 429 on rejection, and failing open when the store throws.

```java
// RateLimiterSpringDemo.java
// A focused, runnable stand-in for the real Spring Boot classes (Filter,
// @Service, @ConfigurationProperties) - same structure as a real Spring
// project, with lightweight substitutes so this runs standalone via `java`.
import java.util.*;

public class RateLimiterSpringDemo {

    // ---------- RateLimitConfig (@ConfigurationProperties in real Spring) ----------
    record RuleConfig(String ruleName, int limit, double refillPerSecond) {}
    static class RateLimitConfig {
        Map<String, List<RuleConfig>> rulesByTier = new HashMap<>();
        RateLimitConfig() {
            rulesByTier.put("free", List.of(new RuleConfig("per-minute", 10, 10.0 / 60)));
            rulesByTier.put("paid", List.of(new RuleConfig("per-minute", 1000, 1000.0 / 60)));
        }
    }

    // ---------- TokenBucket (from the deep-dive facet) ----------
    static class TokenBucket {
        double capacity, tokens, refillRatePerSecond;
        long lastRefillAtMs;
        TokenBucket(double capacity, double refillRatePerSecond, long nowMs) {
            this.capacity = capacity; this.tokens = capacity;
            this.refillRatePerSecond = refillRatePerSecond; this.lastRefillAtMs = nowMs;
        }
        synchronized boolean allow(long nowMs) {
            double elapsed = (nowMs - lastRefillAtMs) / 1000.0;
            tokens = Math.min(capacity, tokens + elapsed * refillRatePerSecond);
            lastRefillAtMs = nowMs;
            if (tokens >= 1.0) { tokens -= 1.0; return true; }
            return false;
        }
        synchronized double remaining() { return tokens; }
    }

    // ---------- RateLimiterService (@Service) ----------
    static class RateLimiterService {
        RateLimitConfig config;
        Map<String, TokenBucket> buckets = new HashMap<>(); // stands in for the shared Redis store
        boolean simulateStoreFailure = false;

        RateLimiterService(RateLimitConfig config) { this.config = config; }

        record CheckResult(boolean allowed, int limit, double remaining) {}

        CheckResult allow(String clientId, String tier, String ruleName, long nowMs) {
            if (simulateStoreFailure) throw new RuntimeException("shared store unreachable");
            RuleConfig rule = config.rulesByTier.get(tier).stream()
                .filter(r -> r.ruleName().equals(ruleName)).findFirst().orElseThrow();
            String key = clientId + ":" + ruleName;
            TokenBucket bucket = buckets.computeIfAbsent(key, k -> new TokenBucket(rule.limit(), rule.refillPerSecond(), nowMs));
            boolean allowed = bucket.allow(nowMs);
            return new CheckResult(allowed, rule.limit(), bucket.remaining());
        }
    }

    // ---------- RateLimitFilter (jakarta.servlet.Filter equivalent) ----------
    static String handleRequest(RateLimiterService service, String clientId, String tier, long nowMs) {
        try {
            RateLimiterService.CheckResult result = service.allow(clientId, tier, "per-minute", nowMs);
            if (!result.allowed()) {
                return "429 Too Many Requests | X-RateLimit-Limit: " + result.limit() +
                    " | X-RateLimit-Remaining: 0";
            }
            return "200 OK | X-RateLimit-Limit: " + result.limit() +
                " | X-RateLimit-Remaining: " + String.format("%.0f", result.remaining());
        } catch (RuntimeException e) {
            // Fail open (NFR-5): store failure means the request proceeds unchecked.
            return "200 OK (FAIL-OPEN: " + e.getMessage() + ", request allowed unchecked)";
        }
    }

    public static void main(String[] args) {
        RateLimitConfig config = new RateLimitConfig();
        RateLimiterService service = new RateLimiterService(config);
        long t = 0;

        System.out.println("Level 1 - basic gating, free-tier client (limit 10/min):");
        for (int i = 1; i <= 11; i++) {
            System.out.println("  request " + i + ": " + handleRequest(service, "c-free-1", "free", t));
        }

        System.out.println("\nLevel 2 - per-tier config: paid client gets a much higher limit:");
        for (int i = 1; i <= 3; i++) {
            System.out.println("  paid client request " + i + ": " + handleRequest(service, "c-paid-1", "paid", t));
        }
        System.out.println("  (free client c-free-1 is unaffected - independent bucket, per FR-3)");

        System.out.println("\nLevel 3 - store failure -> fail open (NFR-5):");
        service.simulateStoreFailure = true;
        System.out.println("  " + handleRequest(service, "c-free-1", "free", t) +
            "  <- allowed despite being at its limit, because the store itself failed");
    }
}
```

**How to run:** `java RateLimiterSpringDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `handleRequest` is called 11 times for client `"c-free-1"` on the `"free"` tier, whose config gives it a limit of 10 per minute. `RateLimiterService.allow(...)` looks up (or lazily creates, via `computeIfAbsent`) a `TokenBucket` keyed by `"c-free-1:per-minute"`, matching the key structure from [data model & schema](0238-rate-limiter-data-model-schema.md). The first 10 calls succeed (the bucket starts full at capacity 10); the 11th finds `tokens < 1.0` and returns `allowed=false`, which `handleRequest` translates into the `429` response with the headers specified in [API design](0236-rate-limiter-api-design.md).
2. **Level 2:** `"c-paid-1"` on the `"paid"` tier looks up a **different** `RuleConfig` (limit 1000, not 10) from the same `RateLimitConfig`, directly implementing FR-4 — the same `RateLimiterService.allow(...)` method handles both tiers identically; only the configuration data differs, exactly as [high-level architecture](0237-rate-limiter-high-level-architecture.md)'s core concept described (FR-4 is a configuration concern, not a different algorithm per tier).
3. **The printed note confirms `"c-free-1"` is unaffected by `"c-paid-1"`'s requests** — since each client's bucket is keyed independently (`clientId + ruleName`), directly satisfying FR-3's per-client independence requirement, verified here by the fact that no shared state connects the two clients' `TokenBucket` instances at all.
4. **Level 3:** `service.simulateStoreFailure = true` causes the next call to `service.allow(...)` to throw immediately, standing in for a real Redis connection failure. `handleRequest`'s `try/catch` block catches this specific exception and returns a `200 OK` with a note explaining the fail-open behavior — the request is let through even though `"c-free-1"` was already at its limit from Level 1's exhaustive testing, because the store itself, not the client's quota, is the reason this request cannot be properly checked.
5. **This fail-open behavior lives entirely in the filter's exception handling** (`handleRequest`'s `catch` block here), not inside `RateLimiterService` itself — a deliberate structural choice: the service's job is to answer the check correctly when it can; the filter's job is to decide what "correctly" means when the check itself is unavailable, which is exactly the separation of concerns NFR-5 calls for.

## 7. Gotchas & takeaways

> **Gotcha:** placing the fail-open `try/catch` inside `RateLimiterService.allow(...)` itself, rather than in the calling filter, would make it easy to accidentally swallow *legitimate* rejections (a real "you are over your limit" result) alongside genuine store failures if the exception handling is not written carefully — keeping the fail-open logic in the filter, wrapping only the call to the service, keeps the failure-handling boundary precise and easy to reason about.

- The filter/interceptor layer is where FR-2 (`429` on rejection), FR-5 (usage headers), and NFR-5 (fail-open) all actually get implemented — controllers stay completely unaware that rate limiting exists, which is the correct separation of concerns for a cross-cutting API-gateway-style concern (see [API gateway & BFF composition](0215-api-gateway-bff-composition.md) for the same principle applied more broadly).
- Load per-tier limits from configuration (`@ConfigurationProperties` in real Spring, `RateLimitConfig` here), never hardcoded in Java — this is what makes FR-4's tier-based limits adjustable without a code deployment.
- This closes out the Rate Limiter case study — the same nine-facet structure applied to the [URL Shortener](0224-url-shortener-functional-requirements.md) applies equally well here, and to the [Pastebin](0242-pastebin-functional-requirements.md) case study that follows.
