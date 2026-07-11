---
card: spring-cloud
gi: 25
slug: fail-fast-retry
title: "Fail-fast & retry"
---

## 1. What it is

`spring.cloud.config.fail-fast` controls whether a Config Client application refuses to start when it can't reach the Config Server (`true`, the fail-fast behavior) or starts anyway with only local configuration (`false`, the default in many setups). Paired with retry settings (`spring.cloud.config.retry.*`), a Config Client can be configured to retry the fetch several times with backoff before giving up, rather than failing on the very first transient connection blip.

```yaml
spring:
  cloud:
    config:
      fail-fast: true
      retry:
        max-attempts: 6
        initial-interval: 1000
        multiplier: 1.5
        max-interval: 10000
```

## 2. Why & when

The previous card's `optional:` prefix on `spring.config.import` was one blunt tool for handling a Config Server that might be unreachable — either fail immediately or silently fall back. `fail-fast` and `retry` together offer a middle ground: treat a genuinely unreachable Config Server as fatal (since many applications simply can't run correctly without their remote configuration), but don't give up on the very first attempt, since a momentary network blip or a Config Server restarting during a rolling deployment shouldn't cause every dependent service's startup to fail.

Reach for `fail-fast`/`retry` configuration when:

- The application genuinely cannot function correctly without its Config Server-sourced configuration, and starting with incomplete local-only config would be worse than not starting at all.
- Config Server outages are sometimes transient (a rolling restart, a brief network partition) and a few retries with backoff would very likely succeed, avoiding an unnecessary hard failure.
- You're tuning startup behavior during a coordinated deployment where the Config Server and its dependent services might restart in close succession, and some tolerance for startup-ordering races is needed.

## 3. Core concept

```
 fail-fast: false (default in many setups)
   Config Server unreachable -> log a warning -> continue startup with LOCAL config only
   Risk: application starts "successfully" but silently missing centrally-managed configuration

 fail-fast: true
   Config Server unreachable -> throw an exception -> application startup FAILS
   Risk: a transient blip fails startup unnecessarily, UNLESS retry is also configured

 fail-fast: true + retry:
   attempt 1 fails -> wait ~1000ms -> attempt 2 fails -> wait ~1500ms -> attempt 3 succeeds -> startup continues
   only if ALL attempts (max-attempts) fail does startup actually fail
```

`fail-fast` alone is a blunt on/off switch; `retry` adds resilience to transient failures before that switch actually trips.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Repeated fetch attempts with increasing backoff intervals, succeeding on a later attempt before the max attempt count is exhausted">
  <rect x="20" y="55" width="100" height="40" rx="6" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">attempt 1</text>

  <rect x="160" y="55" width="100" height="40" rx="6" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="210" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">attempt 2</text>

  <rect x="330" y="55" width="100" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">attempt 3 OK</text>

  <line x1="120" y1="75" x2="150" y2="75" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a45)"/>
  <text x="135" y="65" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">1s</text>
  <line x1="260" y1="75" x2="320" y2="75" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a45)"/>
  <text x="290" y="65" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">1.5s</text>

  <defs><marker id="a45" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each failed attempt waits progressively longer before the next, giving a transient outage a real chance to resolve before startup is declared failed.

## 5. Runnable example

The scenario: a payment service starting up against a flaky Config Server, evolving from a single unretried fetch attempt that fails outright on any transient blip, to a retry loop with exponential backoff, to a full fail-fast-plus-retry configuration that succeeds after a temporary outage resolves partway through the retry sequence.

### Level 1 — Basic

Show a single, unretried fetch attempt — fails immediately on any transient failure.

```java
public class FailFastRetryLevel1 {
    public static void main(String[] args) {
        FlakyConfigServer server = new FlakyConfigServer(2); // fails the first 2 calls, succeeds on the 3rd

        try {
            String config = server.fetch(); // ONE attempt, no retry
            System.out.println("Fetched: " + config);
        } catch (RuntimeException e) {
            System.out.println("Startup FAILED (no retry attempted): " + e.getMessage());
        }
    }
}

class FlakyConfigServer {
    private int callCount = 0;
    private final int failuresBeforeSuccess;
    FlakyConfigServer(int failuresBeforeSuccess) { this.failuresBeforeSuccess = failuresBeforeSuccess; }

    String fetch() {
        callCount++;
        if (callCount <= failuresBeforeSuccess) throw new RuntimeException("connection refused (attempt " + callCount + ")");
        return "{ db.pool.size: 50 }";
    }
}
```

How to run: `java FailFastRetryLevel1.java`

`server.fetch()` is called exactly once — since the server is configured to fail its first two calls, this single attempt fails, and startup gives up immediately even though the very next attempt would have succeeded.

### Level 2 — Intermediate

Add a retry loop with exponential backoff, giving the transient failure a real chance to resolve before giving up.

```java
public class FailFastRetryLevel2 {
    public static void main(String[] args) throws InterruptedException {
        FlakyConfigServer server = new FlakyConfigServer(2);
        String config = fetchWithRetry(server, 6, 1000, 1.5);
        System.out.println("Fetched: " + config);
    }

    static String fetchWithRetry(FlakyConfigServer server, int maxAttempts, long initialIntervalMs, double multiplier) throws InterruptedException {
        long interval = initialIntervalMs;
        RuntimeException lastFailure = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return server.fetch();
            } catch (RuntimeException e) {
                lastFailure = e;
                System.out.println("Attempt " + attempt + " failed: " + e.getMessage() + " (retrying in " + interval + "ms)");
                Thread.sleep(0); // simulated -- real code would sleep 'interval' ms here
                interval = (long) (interval * multiplier);
            }
        }
        throw new IllegalStateException("Config Server unreachable after " + maxAttempts + " attempts", lastFailure);
    }
}

class FlakyConfigServer {
    private int callCount = 0;
    private final int failuresBeforeSuccess;
    FlakyConfigServer(int failuresBeforeSuccess) { this.failuresBeforeSuccess = failuresBeforeSuccess; }
    String fetch() {
        callCount++;
        if (callCount <= failuresBeforeSuccess) throw new RuntimeException("connection refused (attempt " + callCount + ")");
        return "{ db.pool.size: 50 }";
    }
}
```

How to run: `java FailFastRetryLevel2.java`

`fetchWithRetry` catches each failure, logs it, computes an increasing backoff interval (`interval * multiplier`), and tries again — by the third attempt, `FlakyConfigServer`'s internal `callCount` has passed its `failuresBeforeSuccess` threshold, so the fetch succeeds and the retry loop returns immediately, without exhausting all six configured attempts.

### Level 3 — Advanced

Show the full `fail-fast=true` behavior: retries are exhausted for a genuinely persistent outage, and startup fails hard with a clear error — contrasted with a transient outage that resolves within the retry budget.

```java
public class FailFastRetryLevel3 {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("--- Scenario A: transient outage, resolves within retry budget ---");
        try {
            String config = fetchWithRetry(new FlakyConfigServer(2), 6, 1000, 1.5);
            System.out.println("Startup SUCCEEDED: " + config);
        } catch (IllegalStateException e) {
            System.out.println("Startup FAILED: " + e.getMessage());
        }

        System.out.println("--- Scenario B: persistent outage, exceeds retry budget ---");
        try {
            String config = fetchWithRetry(new FlakyConfigServer(10), 6, 1000, 1.5); // needs 10 successes, only get 6 attempts
            System.out.println("Startup SUCCEEDED: " + config);
        } catch (IllegalStateException e) {
            System.out.println("Startup FAILED (fail-fast=true): " + e.getMessage());
        }
    }

    static String fetchWithRetry(FlakyConfigServer server, int maxAttempts, long initialIntervalMs, double multiplier) throws InterruptedException {
        long interval = initialIntervalMs;
        RuntimeException lastFailure = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return server.fetch();
            } catch (RuntimeException e) {
                lastFailure = e;
                interval = (long) (interval * multiplier);
            }
        }
        // fail-fast=true: after exhausting all attempts, startup fails HARD rather than continuing with local-only config.
        throw new IllegalStateException("Config Server unreachable after " + maxAttempts + " attempts", lastFailure);
    }
}

class FlakyConfigServer {
    private int callCount = 0;
    private final int failuresBeforeSuccess;
    FlakyConfigServer(int failuresBeforeSuccess) { this.failuresBeforeSuccess = failuresBeforeSuccess; }
    String fetch() {
        callCount++;
        if (callCount <= failuresBeforeSuccess) throw new RuntimeException("connection refused (attempt " + callCount + ")");
        return "{ db.pool.size: 50 }";
    }
}
```

How to run: `java FailFastRetryLevel3.java`

Scenario A's `FlakyConfigServer` needs only 2 failures before succeeding — well within the 6-attempt budget — so `fetchWithRetry` returns successfully partway through. Scenario B's server needs 10 successive failures before succeeding, exceeding the same 6-attempt budget entirely — every attempt fails, the loop exhausts `maxAttempts`, and `fetchWithRetry` throws, which is exactly the `fail-fast=true` behavior: startup genuinely fails rather than silently continuing with incomplete configuration.

## 6. Walkthrough

Execution starts in `main` for Level 3. Scenario A constructs `FlakyConfigServer(2)` and calls `fetchWithRetry` with a 6-attempt budget. Internally, attempts 1 and 2 throw (since `callCount <= 2`), and attempt 3 succeeds (`callCount` is now 3, exceeding `failuresBeforeSuccess`):

```
--- Scenario A: transient outage, resolves within retry budget ---
Startup SUCCEEDED: { db.pool.size: 50 }
```

Scenario B constructs `FlakyConfigServer(10)` — this server needs 10 consecutive failed calls before it would ever succeed — and calls `fetchWithRetry` with the *same* 6-attempt budget. All 6 attempts fail (`callCount` only reaches 6, still `<= 10`), the `for` loop completes without ever returning, and the function falls through to `throw new IllegalStateException(...)`:

```
--- Scenario B: persistent outage, exceeds retry budget ---
Startup FAILED (fail-fast=true): Config Server unreachable after 6 attempts
```

In a real Spring Cloud application, this exact distinction matters operationally: `fail-fast=true` combined with a reasonably generous retry budget handles the common case (a brief Config Server restart during a rolling deployment) gracefully, while still guaranteeing that a genuinely broken or unreachable Config Server causes a clear, immediate startup failure — rather than either silently starting with incomplete configuration, or failing unnecessarily on the very first transient blip.

## 7. Gotchas & takeaways

> Gotcha: `fail-fast=true` without a correspondingly generous retry configuration can make ordinary rolling deployments unreliable — if the Config Server itself is being redeployed at roughly the same time as its dependent services, a too-small retry budget can cause a cascade of unnecessary startup failures across the fleet, even though the outage was always going to be brief.

> Gotcha: `fail-fast=false` (or omitting the setting, depending on version defaults) can mask a genuine Config Server outage as a "successful" but silently misconfigured startup — an operator seeing all services report healthy has no signal that they're actually running on stale or incomplete local-only configuration, unless something else (a metric, a specific health check) surfaces that gap.

- `fail-fast` decides whether an unreachable Config Server is a fatal startup error (`true`) or a silently degraded fallback to local-only configuration (`false`) — the right choice depends on whether the application can function correctly without its remote configuration.
- `retry` settings add resilience against transient Config Server unavailability, giving several attempts with increasing backoff before `fail-fast` actually triggers a hard failure.
- The combination handles the common case (brief outages during rolling deployments) gracefully while still guaranteeing a genuine, persistent outage causes a clear failure rather than a silent misconfiguration.
- Retry budgets need to be tuned against realistic deployment timing — too small risks unnecessary failures during ordinary rolling restarts, too large delays detecting a genuine, persistent outage.
