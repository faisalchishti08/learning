---
card: microservices
gi: 78
slug: http-verbs-status-code-semantics
title: "HTTP verbs & status code semantics"
---

## 1. What it is

HTTP verbs (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) each carry a precise, standardized meaning — and two of them carry an additional guarantee that matters enormously in distributed systems: **idempotency**, meaning calling the operation multiple times with the same input has the same effect as calling it once. `GET`, `PUT`, and `DELETE` are idempotent; `POST` and `PATCH` generally are not. Status codes similarly fall into standardized bands: `2xx` for success, `4xx` for a client error (the caller did something wrong), `5xx` for a server error (something went wrong on the server's side), each carrying meaning any HTTP-aware tool can act on without understanding your specific application.

## 2. Why & when

Getting verb semantics right matters most under retry logic, which every microservices system needs somewhere (network calls fail transiently). A client that doesn't know whether it's safe to retry a request — because it doesn't know whether the verb is idempotent — either risks double-processing a non-idempotent request (charging a customer twice) or gives up too conservatively on a safe-to-retry one. Getting status code bands right matters for the same reason at the infrastructure layer: a load balancer or client library can automatically retry a request that failed with `503 Service Unavailable` (a transient server problem) but should *not* automatically retry one that failed with `400 Bad Request` (retrying the exact same malformed request will fail identically every time).

Apply verb and status-code semantics correctly from day one of designing a service's API — infrastructure and client libraries throughout a microservices system make real behavioral decisions (retry, don't retry; safe to call twice, don't call twice) based on exactly these signals.

## 3. Core concept

Idempotency is a property of the *operation's effect*, not of how many times you happen to call it — calling an idempotent operation N times leaves the system in the same state as calling it once.

```
GET    /orders/42          idempotent: reading twice changes nothing        -- safe to retry blindly
PUT    /orders/42          idempotent: replacing with the SAME body twice   -- safe to retry blindly
                            leaves the resource in the same final state
DELETE /orders/42          idempotent: deleting twice leaves it "gone"      -- safe to retry blindly
                            both times (2nd call: 404, but same end state)
POST   /orders             NOT idempotent: posting twice creates TWO orders -- unsafe to retry blindly
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A comparison showing a PUT request applied twice leaving the resource in the same state, versus a POST request applied twice creating two separate resources">
  <text x="160" y="20" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">PUT /orders/42 (idempotent) x2</text>
  <rect x="20" y="35" width="280" height="35" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="57" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order 42: status=CANCELLED</text>
  <text x="160" y="85" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">call again -&gt; SAME final state</text>
  <rect x="20" y="95" width="280" height="35" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="117" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order 42: status=CANCELLED</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">POST /orders (NOT idempotent) x2</text>
  <rect x="340" y="35" width="280" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="57" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order 43 created</text>
  <text x="480" y="85" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">call again -&gt; a SECOND resource!</text>
  <rect x="340" y="95" width="280" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="117" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">order 44 created (duplicate!)</text>
</svg>

Idempotent operations converge to the same end state on retry; POST does not.

## 5. Runnable example

Scenario: an order service exposed to a flaky network, first showing a naive retry loop applied blindly to a `POST`, causing duplicate orders, then fixed by checking the verb's idempotency before retrying, then extended to model status-code-aware retry logic that distinguishes retryable server errors from non-retryable client errors.

### Level 1 — Basic

```java
// File: BlindRetryDuplicatesOrders.java -- retrying a POST blindly on
// any failure creates DUPLICATE resources -- POST is NOT idempotent.
import java.util.*;

public class BlindRetryDuplicatesOrders {
    static List<String> orders = new ArrayList<>();
    static int attemptCount = 0;

    static boolean postOrder(String sku) {
        attemptCount++;
        orders.add(sku + "-order-" + attemptCount);
        // simulate: the RESPONSE is lost on the wire on the first attempt,
        // even though the order WAS created server-side
        return attemptCount > 1; // "succeeds" (from caller's view) only on retry
    }

    static void blindRetry(String sku) {
        boolean success = postOrder(sku);
        while (!success) {
            System.out.println("  [no response received, retrying POST...]");
            success = postOrder(sku);
        }
    }

    public static void main(String[] args) {
        blindRetry("widget");
        System.out.println("Orders created: " + orders);
    }
}
```

**How to run:** `javac BlindRetryDuplicatesOrders.java && java BlindRetryDuplicatesOrders` (JDK 17+).

Expected output:
```
  [no response received, retrying POST...]
Orders created: [widget-order-1, widget-order-2]
```

The first `POST` actually succeeded server-side (order 1 was created); the client just never saw the response, so it retried — and because `POST` is not idempotent, that retry created a *second*, duplicate order.

### Level 2 — Intermediate

```java
// File: IdempotencyAwareRetry.java -- check the VERB's idempotency
// before deciding whether blind retry is safe -- GET/PUT/DELETE: safe.
// POST/PATCH: unsafe without extra protection.
import java.util.*;

public class IdempotencyAwareRetry {
    static Set<String> idempotentVerbs = Set.of("GET", "PUT", "DELETE");

    static boolean isSafeToBlindlyRetry(String verb) {
        return idempotentVerbs.contains(verb);
    }

    public static void main(String[] args) {
        List<String> verbs = List.of("GET", "POST", "PUT", "DELETE", "PATCH");
        for (String verb : verbs) {
            boolean safe = isSafeToBlindlyRetry(verb);
            System.out.println(verb + ": " + (safe ? "safe to retry blindly" : "UNSAFE to retry blindly"));
        }
    }
}
```

**How to run:** `javac IdempotencyAwareRetry.java && java IdempotencyAwareRetry` (JDK 17+).

Expected output:
```
GET: safe to retry blindly
POST: UNSAFE to retry blindly
PUT: safe to retry blindly
DELETE: safe to retry blindly
PATCH: UNSAFE to retry blindly
```

### Level 3 — Advanced

```java
// File: StatusCodeAwareRetry.java -- also decide retry behavior based on
// the STATUS CODE returned: retry a 5xx (transient server problem), but
// NEVER retry a 4xx (retrying the same bad request fails identically).
import java.util.*;

public class StatusCodeAwareRetry {
    record Attempt(int statusCode) {}

    static boolean shouldRetry(int statusCode) {
        if (statusCode >= 500) return true;  // 5xx: server-side, possibly transient -- retry
        if (statusCode >= 400) return false; // 4xx: client error -- retrying won't help
        return false; // 2xx: already succeeded, nothing to retry
    }

    static List<Attempt> callWithRetry(List<Integer> simulatedResponses, int maxAttempts) {
        List<Attempt> log = new ArrayList<>();
        for (int i = 0; i < simulatedResponses.size() && i < maxAttempts; i++) {
            int status = simulatedResponses.get(i);
            log.add(new Attempt(status));
            if (!shouldRetry(status)) break; // either succeeded (2xx) or a non-retryable 4xx
        }
        return log;
    }

    public static void main(String[] args) {
        System.out.println("Scenario A: transient 503, then success");
        List<Attempt> a = callWithRetry(List.of(503, 503, 200), 5);
        a.forEach(att -> System.out.println("  attempt -> " + att.statusCode()));

        System.out.println("Scenario B: 400 Bad Request (must NOT retry)");
        List<Attempt> b = callWithRetry(List.of(400, 200), 5); // 200 here would NEVER be reached
        b.forEach(att -> System.out.println("  attempt -> " + att.statusCode()));
    }
}
```

**How to run:** `javac StatusCodeAwareRetry.java && java StatusCodeAwareRetry` (JDK 17+).

Expected output:
```
Scenario A: transient 503, then success
  attempt -> 503
  attempt -> 503
  attempt -> 200
Scenario B: 400 Bad Request (must NOT retry)
  attempt -> 400
```

## 6. Walkthrough

1. **Level 1** — `postOrder` appends a new entry to `orders` on *every* call and only reports "success" (from the caller's simulated point of view) starting on the second attempt, standing in for a response getting lost on the wire after the server already processed the request. `blindRetry` loops until `success` is `true`, calling `postOrder` twice — and because each call unconditionally appends a new order, `main` prints two distinct order entries (`widget-order-1` and `widget-order-2`) for what was meant to be one logical order — a real, damaging duplicate caused purely by retrying a non-idempotent verb without any safeguard.
2. **Level 2 — checking idempotency before retrying** — `isSafeToBlindlyRetry` simply checks membership in `idempotentVerbs`. Looping over all five standard verbs and printing the verdict for each reproduces exactly the [core concept](#3-core-concept)'s classification: `GET`, `PUT`, `DELETE` are safe; `POST`, `PATCH` are flagged unsafe. This is the check that, applied to Level 1's scenario, would have told the client *not* to blindly retry the `POST` — the duplicate-order bug is a direct consequence of skipping exactly this check.
3. **Level 3 — factoring in the status code too** — `shouldRetry` adds a second dimension: even for a verb where retrying is generally acceptable, the *specific failure* still matters. A `5xx` status suggests a transient, server-side problem (worth retrying); a `4xx` status means the client's own request was malformed or unauthorized, so retrying the identical request will just fail identically again — retrying wastes time and can even look like a misbehaving client to the server.
4. **Tracing Scenario A** — `callWithRetry(List.of(503, 503, 200), 5)` processes each simulated response in order: attempt 1 returns `503`, `shouldRetry(503)` is `true` (>= 500), so the loop continues; attempt 2 also returns `503`, same result, loop continues; attempt 3 returns `200`, `shouldRetry(200)` is `false`, so the loop breaks. All three attempts are logged and printed — the caller correctly persisted through two transient failures to reach success.
5. **Tracing Scenario B** — `callWithRetry(List.of(400, 200), 5)` processes attempt 1, which returns `400`. `shouldRetry(400)` is `false` (it's a `4xx`, not `5xx`), so the loop breaks *immediately* — the `200` at index 1 in the simulated response list is never reached, and only one attempt appears in the printed log. This is the deliberate, correct behavior: even though a hypothetical retry might have looked like it would "succeed" in this contrived setup, real `4xx` errors mean the *same* malformed request would fail identically forever, so continuing to retry would be pure waste.

## 7. Gotchas & takeaways

> **Gotcha:** `PATCH` is often treated as idempotent by developers because it "feels like PUT," but a `PATCH` describing a *relative* change (e.g., "increment the quantity by 1") is not idempotent — applying it twice doubles the increment. Only treat `PATCH` as idempotent when its body describes an absolute, final-state change; when in doubt, treat it as unsafe to retry blindly, same as `POST`.

- `GET`, `PUT`, and `DELETE` are idempotent by HTTP specification; `POST` is not; `PATCH` depends on what the patch actually describes.
- Blindly retrying a non-idempotent request on failure risks duplicating its effect — use [idempotency keys](0083-idempotency-keys-for-safe-retries.md) when a non-idempotent operation genuinely needs safe retries.
- Status code bands carry their own retry semantics: `5xx` (server-side, potentially transient) is generally safe to retry; `4xx` (client-side, the request itself is wrong) should not be retried unmodified.
- Infrastructure components — load balancers, HTTP client libraries, service meshes — commonly implement automatic retry logic based on exactly these two signals, so getting verb and status code semantics right in your own API directly affects how safely that infrastructure can help you.
- See [Idempotency of operations](0082-idempotency-of-operations.md) for a deeper treatment of designing operations to be safely retryable in the first place.
