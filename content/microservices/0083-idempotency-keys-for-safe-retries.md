---
card: microservices
gi: 83
slug: idempotency-keys-for-safe-retries
title: "Idempotency keys for safe retries"
---

## 1. What it is

An idempotency key is a unique identifier — usually a client-generated UUID — sent with a request (typically in an `Idempotency-Key` HTTP header) so that the server can recognize and safely deduplicate retries of what is logically the *same* request, even though the operation being requested (like creating an order) isn't naturally idempotent on its own. This is the practical, HTTP-level implementation of the uniqueness-check technique introduced in [idempotency of operations](0082-idempotency-of-operations.md), standardized as a request header rather than a bespoke application field.

## 2. Why & when

A `POST /orders` call that creates a new order is not idempotent by nature — calling it twice creates two orders. But a client that sends the request and never receives a response (timeout, dropped connection) genuinely cannot tell whether the order was created or not, and needs a safe way to retry. An idempotency key resolves this: the client generates one key per logical attempt to place *this* order, sends it with every retry of that same attempt, and the server, upon seeing a key it has already processed, returns the original result instead of creating a second order.

Use idempotency keys for any `POST` (or non-idempotent `PATCH`) endpoint where a client might reasonably need to retry after an ambiguous failure — payment processing, order creation, any operation with a real-world side effect that must not be duplicated. It's less necessary for naturally idempotent endpoints (`GET`, `PUT`, `DELETE`), which don't need this extra mechanism at all.

## 3. Core concept

The server stores a mapping from idempotency key to the result it produced the first time it saw that key; on any subsequent request with the same key, it returns the stored result directly, without re-executing the operation.

```
POST /orders
Idempotency-Key: 7f3e9a2b-...
                    |
        seen before? --- no  --> execute, store (key -> result), return result
                    |
                   yes  --> return the STORED result, do NOT re-execute
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two identical POST requests with the same idempotency key: the first executes and stores the result, the second returns the stored result without re-executing">
  <rect x="20" y="20" width="270" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Request 1: Idempotency-Key: K1</text>
  <text x="155" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">key not seen -&gt; EXECUTE, store result</text>
  <text x="155" y="78" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">201 Created, order=ORD-1</text>

  <rect x="350" y="20" width="270" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Request 2 (retry): Idempotency-Key: K1</text>
  <text x="485" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">key ALREADY seen -&gt; skip execution</text>
  <text x="485" y="78" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">201 Created, order=ORD-1 (same!)</text>

  <rect x="200" y="120" width="240" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="145" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">idempotency key store: {K1 -&gt; ORD-1}</text>
  <line x1="155" y1="90" x2="280" y2="120" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="485" y1="90" x2="360" y2="120" stroke="#8b949e" stroke-width="1.2"/>
</svg>

The idempotency key store is the single source of truth for whether a given logical request has already been executed.

## 5. Runnable example

Scenario: an order-creation endpoint, first with no idempotency-key handling (a retry creates a duplicate), then fixed by storing and checking keys before executing, then extended to also detect a client mistake — reusing the same key with genuinely different request data — which should be rejected, not silently accepted as if it were a legitimate retry.

### Level 1 — Basic

```java
// File: NoIdempotencyKey.java -- creating an order with NO idempotency
// protection -- a retry after a lost response creates a duplicate.
import java.util.*;

public class NoIdempotencyKey {
    static List<String> orders = new ArrayList<>();
    static int nextId = 1;

    static String createOrder(String sku) {
        String orderId = "ORD-" + (nextId++);
        orders.add(orderId + ":" + sku);
        return orderId;
    }

    public static void main(String[] args) {
        String first = createOrder("widget");
        System.out.println("Created: " + first);
        System.out.println("(response lost, client retries the SAME logical request)");
        String retried = createOrder("widget");
        System.out.println("Created: " + retried);
        System.out.println("Total orders: " + orders.size() + " " + orders);
    }
}
```

**How to run:** `javac NoIdempotencyKey.java && java NoIdempotencyKey` (JDK 17+).

Expected output:
```
Created: ORD-1
(response lost, client retries the SAME logical request)
Created: ORD-2
Total orders: 2 [ORD-1:widget, ORD-2:widget]
```

### Level 2 — Intermediate

```java
// File: WithIdempotencyKey.java -- the client sends an Idempotency-Key
// with every attempt of the SAME logical request; the server stores and
// checks it before executing.
import java.util.*;

public class WithIdempotencyKey {
    record HttpRequest(String idempotencyKey, String sku) {}
    record HttpResponse(int status, String orderId) {}

    static Map<String, String> resultsByKey = new HashMap<>(); // idempotencyKey -> orderId
    static List<String> orders = new ArrayList<>();
    static int nextId = 1;

    static HttpResponse createOrder(HttpRequest req) {
        if (resultsByKey.containsKey(req.idempotencyKey())) {
            String existing = resultsByKey.get(req.idempotencyKey());
            System.out.println("  [key " + req.idempotencyKey() + " already processed -- returning stored result]");
            return new HttpResponse(201, existing);
        }
        String orderId = "ORD-" + (nextId++);
        orders.add(orderId + ":" + req.sku());
        resultsByKey.put(req.idempotencyKey(), orderId);
        return new HttpResponse(201, orderId);
    }

    public static void main(String[] args) {
        String key = "7f3e9a2b-client-generated";
        HttpResponse first = createOrder(new HttpRequest(key, "widget"));
        System.out.println("Response: " + first.status() + " " + first.orderId());

        System.out.println("(response lost, client retries with the SAME key)");
        HttpResponse retried = createOrder(new HttpRequest(key, "widget"));
        System.out.println("Response: " + retried.status() + " " + retried.orderId());

        System.out.println("Total orders: " + orders.size() + " " + orders);
    }
}
```

**How to run:** `javac WithIdempotencyKey.java && java WithIdempotencyKey` (JDK 17+).

Expected output:
```
Response: 201 ORD-1
(response lost, client retries with the SAME key)
  [key 7f3e9a2b-client-generated already processed -- returning stored result]
Response: 201 ORD-1
Total orders: 1 [ORD-1:widget]
```

### Level 3 — Advanced

```java
// File: DetectingKeyReuseWithDifferentPayload.java -- guard against a
// CLIENT MISTAKE: reusing the same idempotency key for a genuinely
// DIFFERENT request body -- this must be REJECTED, not silently treated
// as a safe retry, since the two requests represent different intents.
import java.util.*;

public class DetectingKeyReuseWithDifferentPayload {
    record HttpRequest(String idempotencyKey, String sku) {}
    record StoredResult(String requestFingerprint, String orderId) {}
    record HttpResponse(int status, String body) {}

    static Map<String, StoredResult> resultsByKey = new HashMap<>();
    static List<String> orders = new ArrayList<>();
    static int nextId = 1;

    static String fingerprint(HttpRequest req) { return req.sku(); } // simplified: hash of the real payload in practice

    static HttpResponse createOrder(HttpRequest req) {
        String fp = fingerprint(req);
        if (resultsByKey.containsKey(req.idempotencyKey())) {
            StoredResult stored = resultsByKey.get(req.idempotencyKey());
            if (!stored.requestFingerprint().equals(fp)) {
                return new HttpResponse(422, "{\"error\":\"idempotency key reused with a different request body\"}");
            }
            return new HttpResponse(201, "{\"orderId\":\"" + stored.orderId() + "\"}"); // genuine retry -- safe
        }
        String orderId = "ORD-" + (nextId++);
        orders.add(orderId + ":" + req.sku());
        resultsByKey.put(req.idempotencyKey(), new StoredResult(fp, orderId));
        return new HttpResponse(201, "{\"orderId\":\"" + orderId + "\"}");
    }

    public static void main(String[] args) {
        String key = "same-key-reused-incorrectly";
        HttpResponse first = createOrder(new HttpRequest(key, "widget"));
        System.out.println("Request A (sku=widget): " + first.status() + " " + first.body());

        HttpResponse second = createOrder(new HttpRequest(key, "gadget")); // SAME key, DIFFERENT sku -- a bug or misuse
        System.out.println("Request B (sku=gadget, same key!): " + second.status() + " " + second.body());
    }
}
```

**How to run:** `javac DetectingKeyReuseWithDifferentPayload.java && java DetectingKeyReuseWithDifferentPayload` (JDK 17+).

Expected output:
```
Request A (sku=widget): 201 {"orderId":"ORD-1"}
Request B (sku=gadget, same key!): 422 {"error":"idempotency key reused with a different request body"}
```

## 6. Walkthrough

1. **Level 1** — `createOrder` has no concept of a key at all; it assigns a new id and appends to `orders` on every call. `main` calls it twice, simulating a lost-response retry, and the final `orders` list shows two separate entries (`ORD-1` and `ORD-2`) for what was meant to be one logical order — the exact duplication problem idempotency keys exist to prevent.
2. **Level 2 — storing and checking the key** — `createOrder` now first checks `resultsByKey.containsKey(req.idempotencyKey())`. `main` sends the *same* `key` on both calls: the first call finds no entry, proceeds to create `ORD-1`, and stores `key -> "ORD-1"`. The second call (the simulated retry) finds `key` already present, prints the "already processed" diagnostic, and returns the *stored* `"ORD-1"` directly, without touching `orders` at all — the final count confirms only one order genuinely exists.
3. **Level 3 — guarding against key misuse** — real systems must also handle a client bug: sending the *same* idempotency key with a *different* request body (which should never happen for a genuine retry of the same logical intent, but can happen due to a client-side error, like reusing a key across two different orders). `fingerprint` computes a simplified stand-in for a real hash of the request payload (here, just the `sku` field); `StoredResult` now stores both the `orderId` *and* the `requestFingerprint` that produced it.
4. **Tracing Request A and Request B** — `createOrder(new HttpRequest(key, "widget"))` finds no existing entry for `key`, computes `fp = "widget"`, creates `ORD-1`, and stores `key -> StoredResult("widget", "ORD-1")`, returning `201` with `ORD-1`. `createOrder(new HttpRequest(key, "gadget"))` reuses the *same* `key`, finds the stored entry, computes the new request's fingerprint as `"gadget"`, and compares it against the stored `"widget"` — they don't match, so the method returns `422` with an explicit error, rather than either creating a second order or silently returning `ORD-1` as if `gadget` and `widget` were the same request.
5. **Why this distinction matters** — silently treating Request B as a safe retry (returning `ORD-1`) would hide a real bug from the client — they asked for a `gadget` order and received confirmation of a `widget` order instead, with no error raised. Silently treating it as a new order (creating `ORD-2`) would defeat the whole purpose of the idempotency key. Returning `422` (or `409 Conflict`, another reasonable choice) makes the conflict explicit and visible, which is the honest, correct response to a request that violates the idempotency key's contract.

## 7. Gotchas & takeaways

> **Gotcha:** idempotency keys need an expiration policy — storing every key forever is an unbounded memory/storage leak. A common approach is to expire stored keys after a window generous enough to cover realistic retry timeframes (minutes to hours), after which a reused key is treated as brand new — a tradeoff between storage cost and how long retry safety is guaranteed.

- The key is generated once by the *client*, per logical attempt, and reused unchanged across every retry of that same attempt — never regenerated inside a retry loop.
- The server's job is to store the key alongside the result it produced, and return that stored result — without re-executing the operation — whenever it sees the same key again.
- Detect and reject key reuse with a genuinely different payload explicitly (a `409`/`422`), rather than silently treating it as either a safe retry or a new operation — both silent options hide a real problem.
- This is the standardized, HTTP-header-based version of the general uniqueness-check technique from [idempotency of operations](0082-idempotency-of-operations.md).
- Idempotency keys need a bounded expiration window — unbounded storage of every key ever seen is not sustainable in a real, long-running service.
