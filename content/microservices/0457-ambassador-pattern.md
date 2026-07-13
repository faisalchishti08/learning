---
card: microservices
gi: 457
slug: ambassador-pattern
title: "Ambassador pattern"
---

## 1. What it is

The **ambassador pattern** is a specialized [sidecar](0456-sidecar-pattern.md) that acts as a local proxy for **outbound** calls to a remote service: the main application talks to the ambassador over a simple local call, and the ambassador handles everything hard about actually reaching the real destination — network addressing, retries, circuit breaking, and failover — entirely on the main application's behalf. Where a general sidecar can handle any cross-cutting concern, an ambassador is specifically about representing a remote dependency locally, so the main application's code stays simple regardless of how complicated reaching that dependency actually is.

## 2. Why & when

You reach for an ambassador when you want to keep an application's code simple and unaware of the operational complexity of reaching a particular remote dependency:

- **Retry, backoff, and circuit-breaking logic is genuinely complex and easy to get subtly wrong.** Implementing it correctly, and consistently, inside every application that calls a given remote service means N chances to get it wrong instead of one shared, well-tested implementation.
- **Endpoint changes shouldn't require an application code change.** If a remote service migrates to a new address, gets a new region, or needs failover to a backup, an ambassador can absorb that change entirely — the application keeps making the exact same local call it always has, unaware anything changed on the other side.
- **Legacy or third-party applications that can't easily be modified** are a classic ambassador use case: rather than changing code you don't control (or can't safely change) to add retries or TLS, you put an ambassador in front of it and let the ambassador add that behavior transparently, from outside the application.
- **You use this pattern specifically for outbound dependency calls** where the calling logic (retries, endpoint selection, protocol translation) is substantial enough to be worth extracting — for a single simple call to a stable, reliable endpoint, an ambassador is unnecessary overhead.

## 3. Core concept

The name comes from a diplomatic ambassador: a country doesn't send every citizen to personally negotiate with a foreign government — it sends one ambassador who handles the complexity of that relationship (protocol, language, evolving political conditions) on everyone's behalf. Citizens interact with their own government simply; the ambassador absorbs the complexity of dealing with the outside world, and if the foreign government's contact point changes, the ambassador adapts without every citizen needing to learn a new procedure.

Concretely, the mechanics are:

1. **The main application calls its local ambassador**, not the remote service directly — usually over `localhost`, the same locality that makes the [sidecar pattern](0456-sidecar-pattern.md) fast and simple.
2. **The ambassador owns the remote endpoint's address and connection details.** The main application's code has no hardcoded remote hostname, port, or protocol specifics — all of that lives in the ambassador.
3. **The ambassador adds resilience transparently** — retrying transient failures, applying a circuit breaker to stop hammering a clearly-down endpoint, and translating protocols if needed — all invisible to the calling application, which just sees either a successful response or, eventually, a failure.
4. **Sustained failure triggers failover, not endless retrying.** A remote endpoint that's down for an hour, not a moment, shouldn't be retried forever against the same dead address — a resilient ambassador detects sustained failure and switches to a backup endpoint on its own, with the main application never learning that anything changed.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The main application calls its local ambassador over localhost; the ambassador owns retries, circuit breaking, and failover, switching from a dead primary endpoint to a backup without the application's code changing">
  <rect x="20" y="70" width="150" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="95" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">order-service</text>
  <text x="95" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same call, always</text>

  <rect x="230" y="70" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="315" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Ambassador</text>
  <text x="315" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">retry, circuit-break, failover</text>

  <line x1="170" y1="100" x2="230" y2="100" stroke="#8b949e" marker-end="url(#a1)"/>
  <text x="200" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">localhost</text>

  <rect x="460" y="30" width="150" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/>
  <text x="535" y="55" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">primary (down)</text>

  <rect x="460" y="130" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="535" y="155" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">backup (healthy)</text>

  <line x1="400" y1="90" x2="460" y2="50" stroke="#f85149" stroke-dasharray="3,2"/>
  <line x1="400" y1="110" x2="460" y2="150" stroke="#6db33f" stroke-width="2" marker-end="url(#a2)"/>

  <text x="315" y="190" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">application code never changes when the ambassador fails over</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
  </defs>
</svg>

The application always makes the same local call; the ambassador owns the remote endpoint's address, retries transient failures, and fails over to a backup on sustained failure, invisibly.

## 5. Runnable example

Scenario: an `order-service` checking inventory stock through an ambassador. We start with the bare local-proxy delegation, add transparent retry logic for transient failures, then handle the hard case: the primary remote endpoint going down permanently, requiring the ambassador to detect sustained failure and fail over to a backup endpoint entirely on its own, with the application's code never changing across any of it.

### Level 1 — Basic

```java
// File: AmbassadorBasic.java -- models the CORE idea: the main application
// talks to a LOCAL companion proxy (the "ambassador") over a simple local
// call, and the ambassador is the ONLY thing that actually knows how to
// reach the real remote service -- its network location, protocol details,
// etc. The app is simplified to "just call the ambassador."
public class AmbassadorBasic {
    // The ambassador: knows the REAL remote address and protocol details.
    static class InventoryServiceAmbassador {
        final String remoteAddress = "inventory-service.prod.internal:8443";

        String checkStock(String sku) {
            System.out.println("[ambassador] forwarding to real remote " + remoteAddress + " for sku=" + sku);
            return "in-stock"; // stand-in for a real network response
        }
    }

    // The main application: only ever talks to its LOCAL ambassador.
    static class OrderServiceApp {
        final InventoryServiceAmbassador ambassador;
        OrderServiceApp(InventoryServiceAmbassador ambassador) { this.ambassador = ambassador; }

        void placeOrder(String sku) {
            System.out.println("[order-service] checking stock for " + sku + " via local ambassador");
            String stockStatus = ambassador.checkStock(sku);
            System.out.println("[order-service] stock status: " + stockStatus);
        }
    }

    public static void main(String[] args) {
        OrderServiceApp app = new OrderServiceApp(new InventoryServiceAmbassador());
        app.placeOrder("sku-123");
    }
}
```

How to run: `java AmbassadorBasic.java`

`OrderServiceApp` holds a reference to `InventoryServiceAmbassador` but never sees `remoteAddress` at all — that detail is entirely private to the ambassador. `placeOrder` just calls `ambassador.checkStock(sku)`, exactly as simply as if inventory checking were a local operation, even though the ambassador is standing in for what would really be a network call to a separate service.

### Level 2 — Intermediate

```java
// File: AmbassadorWithRetry.java -- the SAME local-proxy idea, now with
// the ambassador transparently adding RETRY logic for transient failures.
// The main application still just calls the ambassador once -- it has NO
// retry code of its own, and never sees the intermediate failures.
import java.util.*;

public class AmbassadorWithRetry {
    static class InventoryServiceAmbassador {
        final String remoteAddress = "inventory-service.prod.internal:8443";
        int callAttempt = 0;

        // Simulates the real remote failing transiently on the first two tries.
        String realRemoteCall(String sku) {
            callAttempt++;
            if (callAttempt < 3) {
                throw new RuntimeException("transient network error (attempt " + callAttempt + ")");
            }
            return "in-stock";
        }

        String checkStock(String sku) {
            int maxRetries = 3;
            for (int attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                    String result = realRemoteCall(sku);
                    System.out.println("[ambassador] attempt " + attempt + " succeeded");
                    return result;
                } catch (RuntimeException e) {
                    System.out.println("[ambassador] attempt " + attempt + " failed (" + e.getMessage() + "), retrying transparently...");
                }
            }
            throw new RuntimeException("all retries exhausted");
        }
    }

    static class OrderServiceApp {
        final InventoryServiceAmbassador ambassador;
        OrderServiceApp(InventoryServiceAmbassador ambassador) { this.ambassador = ambassador; }

        void placeOrder(String sku) {
            // The app calls the ambassador exactly ONCE -- no retry loop here at all.
            String stockStatus = ambassador.checkStock(sku);
            System.out.println("[order-service] stock status: " + stockStatus + " (app never saw the retries)");
        }
    }

    public static void main(String[] args) {
        OrderServiceApp app = new OrderServiceApp(new InventoryServiceAmbassador());
        app.placeOrder("sku-123");
    }
}
```

How to run: `java AmbassadorWithRetry.java`

`realRemoteCall` fails on its first two invocations, simulating a transient network blip. `checkStock` retries up to `maxRetries` times internally, printing each attempt — but `OrderServiceApp.placeOrder` calls `ambassador.checkStock(sku)` exactly once, and by the time it gets a return value, all the retrying has already happened invisibly. The application's code has no `for` loop, no retry count, no knowledge that anything failed at all.

### Level 3 — Advanced

```java
// File: AmbassadorWithFailoverAdvanced.java -- the SAME retrying
// ambassador, now handling a PRODUCTION-FLAVORED hard case: the PRIMARY
// remote endpoint doesn't just have a transient blip -- it goes down
// PERMANENTLY (a real outage, a region failure, a migration). Retrying the
// same dead endpoint forever would never succeed. The ambassador must
// detect sustained failure and FAIL OVER to a backup endpoint entirely on
// its own -- the main application's code never changes, never learns about
// the new address, and never even knows a failover happened.
public class AmbassadorWithFailoverAdvanced {
    static class InventoryServiceAmbassador {
        String currentEndpoint = "inventory-primary.prod.internal:8443";
        final String backupEndpoint = "inventory-backup.prod.internal:8443";
        int consecutiveFailuresOnCurrent = 0;
        static final int FAILOVER_THRESHOLD = 2;
        static final int MAX_ATTEMPTS_PER_ENDPOINT = 2;

        // The primary is permanently down; the backup always works.
        String realRemoteCall(String endpoint, String sku) {
            if (endpoint.equals("inventory-primary.prod.internal:8443")) {
                throw new RuntimeException("connection refused (endpoint down)");
            }
            return "in-stock";
        }

        String checkStock(String sku) {
            for (int endpointsTried = 0; endpointsTried < 2; endpointsTried++) {
                for (int attempt = 1; attempt <= MAX_ATTEMPTS_PER_ENDPOINT; attempt++) {
                    try {
                        String result = realRemoteCall(currentEndpoint, sku);
                        consecutiveFailuresOnCurrent = 0;
                        System.out.println("[ambassador] succeeded via " + currentEndpoint);
                        return result;
                    } catch (RuntimeException e) {
                        consecutiveFailuresOnCurrent++;
                        System.out.println("[ambassador] call to " + currentEndpoint + " failed (" + e.getMessage()
                                + "), consecutiveFailures=" + consecutiveFailuresOnCurrent);
                    }
                }
                if (consecutiveFailuresOnCurrent >= FAILOVER_THRESHOLD && !currentEndpoint.equals(backupEndpoint)) {
                    System.out.println("[ambassador] " + consecutiveFailuresOnCurrent + " consecutive failures on " + currentEndpoint
                            + " -- FAILING OVER to " + backupEndpoint + " (app code unaware)");
                    currentEndpoint = backupEndpoint;
                    consecutiveFailuresOnCurrent = 0;
                }
            }
            throw new RuntimeException("all endpoints exhausted");
        }
    }

    static class OrderServiceApp {
        final InventoryServiceAmbassador ambassador;
        OrderServiceApp(InventoryServiceAmbassador ambassador) { this.ambassador = ambassador; }

        void placeOrder(String orderLabel, String sku) {
            // Identical call, every time -- the app's code never changes.
            String stockStatus = ambassador.checkStock(sku);
            System.out.println("[order-service] " + orderLabel + " stock status: " + stockStatus);
        }
    }

    public static void main(String[] args) {
        InventoryServiceAmbassador ambassador = new InventoryServiceAmbassador();
        OrderServiceApp app = new OrderServiceApp(ambassador);

        System.out.println("--- order-1: primary is down, ambassador retries then fails over ---");
        app.placeOrder("order-1", "sku-123");

        System.out.println();
        System.out.println("--- order-2: ambassador already remembers the backup, no retries needed ---");
        app.placeOrder("order-2", "sku-456");
    }
}
```

How to run: `java AmbassadorWithFailoverAdvanced.java`

`currentEndpoint` is mutable state that lives entirely inside the ambassador — `OrderServiceApp.placeOrder` is byte-for-byte identical between `order-1` and `order-2`, even though the actual remote address being used changes underneath it. `checkStock`'s outer loop tries up to two endpoints: the current one first, and if `consecutiveFailuresOnCurrent` crosses `FAILOVER_THRESHOLD`, it permanently switches `currentEndpoint` to `backupEndpoint` before the loop's second iteration, which then succeeds.

## 6. Walkthrough

Trace `AmbassadorWithFailoverAdvanced.main` in order. **First**, `app.placeOrder("order-1", "sku-123")` calls `ambassador.checkStock("sku-123")`. The outer loop begins with `endpointsTried = 0` and `currentEndpoint` still pointing at the primary.

**Next**, the inner loop runs two attempts against the primary. `realRemoteCall(currentEndpoint, "sku-123")` throws both times, since `currentEndpoint` equals the hardcoded dead-primary string. Each catch increments `consecutiveFailuresOnCurrent`, reaching `1` then `2`.

**Then**, after the inner loop exhausts its two attempts, the failover check runs: `consecutiveFailuresOnCurrent (2) >= FAILOVER_THRESHOLD (2)` is `true`, and `currentEndpoint` doesn't yet equal `backupEndpoint`, so the failover branch executes — `currentEndpoint` is reassigned to `backupEndpoint`, and `consecutiveFailuresOnCurrent` resets to `0`.

**After that**, the outer loop's second iteration (`endpointsTried = 1`) begins, and the inner loop runs again — but now `currentEndpoint` is the backup, so `realRemoteCall` succeeds on the very first attempt, returning `"in-stock"` and printing the success line. `checkStock` returns immediately, and `placeOrder` prints the final stock status for `order-1`.

**Finally**, `app.placeOrder("order-2", "sku-456")` runs against the *same* `ambassador` instance, whose `currentEndpoint` field is still set to `backupEndpoint` from the previous call — the failover decision persisted. The very first attempt succeeds immediately, with no retries and no failover logic re-triggered, since the ambassador already "remembers" that the primary is bad. `OrderServiceApp.placeOrder` is completely unaware any of this happened across either call.

```
--- order-1: primary is down, ambassador retries then fails over ---
[ambassador] call to inventory-primary.prod.internal:8443 failed (connection refused (endpoint down)), consecutiveFailures=1
[ambassador] call to inventory-primary.prod.internal:8443 failed (connection refused (endpoint down)), consecutiveFailures=2
[ambassador] 2 consecutive failures on inventory-primary.prod.internal:8443 -- FAILING OVER to inventory-backup.prod.internal:8443 (app code unaware)
[ambassador] succeeded via inventory-backup.prod.internal:8443
[order-service] order-1 stock status: in-stock

--- order-2: ambassador already remembers the backup, no retries needed ---
[ambassador] succeeded via inventory-backup.prod.internal:8443
[order-service] order-2 stock status: in-stock
```

## 7. Gotchas & takeaways

> An ambassador that retries forever against a permanently dead endpoint is worse than one with no retry logic at all: every request pays the full retry latency before eventually failing, turning a clean, fast failure into a slow, resource-consuming one. Sustained-failure detection and failover — not just retry count — is what actually protects the application from a real, lasting outage.

- The defining property of an ambassador is that it represents an *outbound* dependency locally — a general [sidecar pattern](0456-sidecar-pattern.md) can handle any cross-cutting concern, inbound or outbound, but an ambassador specifically stands in for "the remote thing I need to call."
- Keep retry counts and circuit-breaker thresholds bounded and deliberate — unbounded retries against a truly dead endpoint waste resources and add latency without ever succeeding, exactly the failure mode the failover logic in Level 3 exists to prevent.
- An ambassador is a particularly good fit for legacy or vendored applications you can't easily modify — it adds resilience and endpoint flexibility entirely from the outside, without touching the application's own code.
- Because the ambassador owns connection-level concerns, changing a remote dependency's address, protocol, or failover topology becomes a change to the ambassador alone — the calling application's code and deploy schedule are completely decoupled from that change.
- Ambassadors and general sidecars are frequently deployed together in the same Pod — a logging sidecar for observability, an mTLS sidecar for inbound security, and an ambassador for a specific outbound dependency can all coexist, each handling its own narrow concern.
