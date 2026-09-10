---
card: system-design
gi: 196
slug: microservices
title: Microservices
---

## 1. What it is

**Microservices** is an architecture style where a system is split into many small, independently deployable services, each owning its own data and communicating over the network (usually HTTP or messaging). Each service is built, tested, deployed, and scaled on its own schedule, by a team that owns it end to end.

## 2. Why & when

A [monolith](0195-monolith-modular-monolith.md) forces every team to share one deploy: one bad change from one team can block everyone else's release, and scaling means scaling the whole application even if only one part is under load. Microservices remove that coupling — the orders team deploys orders independently of the payments team, and you scale only the service that needs it.

That independence has a real cost: every call between services now crosses a network, which can fail, time out, or arrive out of order, and data that used to be one database transaction is now spread across services with no single transaction to hold it together. Use microservices when you have multiple teams that need to ship independently, or components with very different scaling needs — not by default. A well-structured [modular monolith](0195-monolith-modular-monolith.md) solves the "tangled code" problem without taking on network unreliability.

## 3. Core concept

- **Service boundary = data boundary.** Each microservice owns its own database. No other service reads that database directly — everything goes through the owning service's API. This is what makes independent deployment possible: nobody else's code depends on your table schema.
- **Network calls replace method calls.** Where a modular monolith calls `paymentsApi.charge(...)` in-process, microservices call it over HTTP or a message queue. This call can now be slow, fail entirely, or partially succeed (the request arrived but the response was lost).
- **No shared transaction.** A single ACID database transaction can no longer span "place the order" and "charge the payment," because they are two separate databases. Multi-service consistency needs patterns like the [saga](0203-saga-orchestration-vs-choreography.md) or the [transactional outbox](0204-transactional-outbox.md).
- **Independent deployability.** The whole point: you can deploy the orders service ten times a day and the payments service once a week, and neither blocks the other, as long as their API contract stays compatible.
- **Service discovery and resilience.** Because services call each other over an unreliable network, you need a way to find a service's current address (service discovery) and a way to handle its failure (timeouts, retries, circuit breakers) — concerns a monolith never had.

## 4. Diagram

```
                     +---------------+
                     |   API Gateway |
                     +-------+-------+
                             |
        +--------------------+---------------------+
        |                    |                      |
        v                    v                      v
 +-------------+      +-------------+        +-------------+
 |   Orders    |      |  Payments   |        |    Users    |
 |  Service    |----->|  Service    |        |  Service    |
 | (own DB)    | HTTP | (own DB)    |        | (own DB)    |
 +-------------+      +-------------+        +-------------+
        |                                            ^
        |                    reads user data          |
        +--------------------------------------------+
                        HTTP (network call, can fail)

 Each box = separate deploy, separate database.
 Each arrow = a network call, not a method call.
```
*Caption: every arrow that used to be a method call inside a monolith is now a network call — the diagram's edges are exactly where new failure modes appear.*

## 5. Runnable example

This models the essential microservices concern — network calls that can fail or time out — inside one file, since a real multi-process demo cannot run as a single script.

**Level 1 — Basic.** Two "services" (plain classes acting as remote stand-ins) communicate through a `NetworkClient` that always succeeds.

**Level 2 — Realistic.** The `NetworkClient` now simulates real network failure and timeout, and the calling service must handle both.

**Level 3 — Advanced.** Add a simple retry with backoff and a circuit breaker that stops calling a service that is failing repeatedly, so one broken service cannot cascade into unbounded retries.

```java
// MicroservicesDemo.java
import java.util.*;

public class MicroservicesDemo {

    // Simulates an unreliable network call between two independently deployed services.
    static class NetworkClient {
        Random rnd = new Random(7);
        double failureRate;
        NetworkClient(double failureRate) { this.failureRate = failureRate; }

        // Returns the response, or throws to simulate a network failure/timeout.
        String call(String service, String request) {
            if (rnd.nextDouble() < failureRate) {
                throw new RuntimeException("network error calling " + service);
            }
            return service + " processed: " + request;
        }
    }

    // ---------- Level 1: basic call, no failure handling ----------
    static void level1() {
        NetworkClient client = new NetworkClient(0.0); // never fails
        String response = client.call("payments-service", "charge $20");
        System.out.println("  [basic] " + response);
    }

    // ---------- Level 2: realistic - handle failure explicitly ----------
    static void level2() {
        NetworkClient client = new NetworkClient(0.5); // fails half the time
        try {
            String response = client.call("payments-service", "charge $20");
            System.out.println("  [realistic] success: " + response);
        } catch (RuntimeException e) {
            System.out.println("  [realistic] call failed: " + e.getMessage() +
                " -> order must be marked PENDING, not CONFIRMED");
        }
    }

    // ---------- Level 3: retry with backoff + circuit breaker ----------
    static class CircuitBreaker {
        int consecutiveFailures = 0;
        final int threshold = 3;
        boolean isOpen = false;

        void recordSuccess() { consecutiveFailures = 0; isOpen = false; }
        void recordFailure() {
            consecutiveFailures++;
            if (consecutiveFailures >= threshold) isOpen = true;
        }
    }

    static String callWithRetryAndBreaker(NetworkClient client, CircuitBreaker breaker,
                                           String service, String request, int maxAttempts) {
        if (breaker.isOpen) {
            return "[circuit open] skipping call to " + service + " - failing fast";
        }
        RuntimeException lastError = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                String result = client.call(service, request);
                breaker.recordSuccess();
                return "attempt " + attempt + ": " + result;
            } catch (RuntimeException e) {
                lastError = e;
                breaker.recordFailure();
                System.out.println("    attempt " + attempt + " failed: " + e.getMessage());
            }
        }
        return "[all " + maxAttempts + " attempts failed] " + lastError.getMessage();
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - basic call:");
        level1();

        System.out.println("\nLevel 2 - realistic call (can fail):");
        level2();

        System.out.println("\nLevel 3 - retry + circuit breaker:");
        NetworkClient flaky = new NetworkClient(0.7); // fails 70% of the time
        CircuitBreaker breaker = new CircuitBreaker();
        for (int i = 1; i <= 4; i++) {
            System.out.println("  request " + i + ":");
            String result = callWithRetryAndBreaker(flaky, breaker, "payments-service", "charge $" + (i * 10), 2);
            System.out.println("  -> " + result);
        }
    }
}
```

**How to run:** `java MicroservicesDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1** calls `client.call(...)` with a `failureRate` of `0.0`, so it always returns a response. This is how a diagram usually presents microservices — as if every call just works.
2. **Level 2** sets `failureRate` to `0.5`. `client.call(...)` throws about half the time. The calling code must now decide what to do: it cannot assume the payment succeeded just because the order service sent the request, so it marks the order `PENDING` instead of `CONFIRMED` on failure — a state a monolith with one transaction would never need.
3. **Level 3 introduces a `CircuitBreaker`.** For each simulated request, `callWithRetryAndBreaker` first checks `breaker.isOpen`. If it is closed, it tries up to `maxAttempts` calls, recording each failure. `flaky`'s `failureRate` is `0.7`, so requests 1 and 2 mostly fail both attempts and push `consecutiveFailures` toward the threshold of 3.
4. **By request 3 or 4**, `consecutiveFailures` has reached the threshold, `breaker.isOpen` becomes `true`, and the next call to `callWithRetryAndBreaker` returns `"[circuit open] skipping call..."` immediately, without touching the network at all — this is the circuit breaker protecting the caller from wasting time retrying a service that is clearly down.
5. This progression — plain call, failure handling, retry-with-circuit-breaker — is exactly the added complexity that microservices bring compared to a monolith's plain in-process method call, which can never fail this way.

## 7. Gotchas & takeaways

> **Gotcha:** adopting microservices without addressing the network-failure and data-consistency problems above just turns one monolith into many, all wired together with unreliable calls and no coordinated transaction. This is often worse than the monolith it replaced.

- Do not split into microservices to "follow best practice" — split because independent deployment or independent scaling solves a real, measured problem you have today.
- Every service boundary must also be a data boundary. Shared databases between "microservices" reintroduce the tangled coupling you were trying to remove.
- Budget real engineering time for retries, timeouts, circuit breakers, and distributed tracing — these are not optional extras, they are the cost of the network calls you introduced.
- A [modular monolith](0195-monolith-modular-monolith.md) gets most of the code-organization benefit of microservices without any of the network cost. Prefer it until you have a specific reason not to.
