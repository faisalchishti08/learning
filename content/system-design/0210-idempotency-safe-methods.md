---
card: system-design
gi: 210
slug: idempotency-safe-methods
title: Idempotency & safe methods
---

## 1. What it is

A method is **safe** if calling it never changes server state — only reads (`GET`, `HEAD`). A method is **idempotent** if calling it multiple times with the same input produces the same end state as calling it once — repeating it is not harmful, even though it may still change state on the first call (`PUT`, `DELETE`, `GET`). `POST` is neither safe nor idempotent by default: calling it twice can create two resources instead of one.

## 2. Why & when

Networks fail in ways that leave the client unsure whether a request succeeded — a timeout might mean the server never got the request, or it might mean the server processed it and the response was lost on the way back. If the client's only safe response to "I don't know if that worked" is to retry, the method's idempotency determines whether that retry is safe.

This matters for every API you build, because clients — and the retry logic inside HTTP libraries, proxies, and load balancers — will retry ambiguous failures whether you plan for it or not. `PUT`, `DELETE`, and `GET` are automatically safe to retry because of their semantics. `POST`, most often used for "create a resource," is not automatically safe — retrying a timed-out `POST /orders` risks creating a second order for the same purchase. Design an idempotency strategy for `POST` wherever a duplicate side effect (a duplicate charge, a duplicate order) would be a real problem.

## 3. Core concept

- **Safe methods change nothing.** `GET /orders/5` can be called any number of times with zero side effects — this is what lets browsers, proxies, and caches retry or prefetch `GET` requests freely.
- **Idempotent methods are safe to retry, but may still write.** `PUT /orders/5` with the same body, called once or five times, leaves the resource in the same final state — it just overwrites it repeatedly with the same value. `DELETE /orders/5` called a second time still leaves the order deleted (the second call may return `404` instead of `200`, but the *state* — "order 5 does not exist" — did not change further).
- **`POST` is neither, by default.** `POST /orders` typically creates a new resource with a server-generated ID on every call — calling it twice creates two resources, not one confirmed resource.
- **Client-generated idempotency keys make `POST` idempotent.** The client generates a unique key (a UUID) per logical operation and sends it in a header (`Idempotency-Key: <uuid>`). The server stores the key alongside the result of the first request; if the same key arrives again, the server returns the stored result instead of creating a second resource.
- **Idempotency key storage needs a expiry.** Keys are usually kept for a bounded window (e.g. 24 hours) — long enough to cover realistic retry scenarios, short enough not to grow the storage unboundedly.

## 4. Diagram

```
  WITHOUT an idempotency key                 WITH an idempotency key

  Client -- POST /orders ------> Server      Client -- POST /orders --------> Server
            (timeout, no response received)            Idempotency-Key: abc-123
  Client -- POST /orders ------> Server                (timeout, no response received)
            (retries, unsure if first        Client -- POST /orders --------> Server
             one succeeded)                             Idempotency-Key: abc-123
                                                          (server sees key "abc-123"
  Result: possibly TWO orders                             already has a stored result -
          created for one purchase                        returns THAT result, creates
                                                            nothing new)

                                             Result: exactly ONE order created,
                                                     regardless of how many retries
```
*Caption: the idempotency key turns a naturally unsafe `POST` into a request the client can retry as many times as needed, with a guaranteed single effect.*

## 5. Runnable example

**Level 1 — Basic.** Show `PUT` and `DELETE` behaving idempotently under repeated calls, and plain `POST` not.

**Level 2 — Intermediate.** Add an idempotency-key store so repeated `POST` calls with the same key return the original result instead of creating a duplicate.

**Level 3 — Advanced.** Simulate a network retry scenario end to end: client sends, "loses" the response, retries with the same key, and still ends up with exactly one created resource.

```java
// IdempotencyDemo.java
import java.util.*;

public class IdempotencyDemo {

    record Order(String id, double amount) {}

    static Map<String, Order> orders = new HashMap<>();
    static int nextOrderId = 1;

    // ---------- Level 1: PUT and DELETE are naturally idempotent; plain POST is not ----------
    static String put(String id, double amount) {
        orders.put(id, new Order(id, amount));
        return "PUT /orders/" + id + " -> 200 OK, state: " + orders.get(id);
    }
    static String delete(String id) {
        boolean existed = orders.remove(id) != null;
        return "DELETE /orders/" + id + " -> " + (existed ? "200 OK, deleted" : "404 Not Found") +
            " (either way, order " + id + " does not exist afterward)";
    }
    static String plainPost(double amount) {
        String id = "ORD-" + (nextOrderId++);
        orders.put(id, new Order(id, amount));
        return "POST /orders -> 201 Created, NEW resource: " + orders.get(id);
    }

    // ---------- Level 2: idempotency-key store makes POST safe to retry ----------
    static Map<String, String> idempotencyStore = new HashMap<>(); // key -> response already given

    static String postWithIdempotencyKey(String idempotencyKey, double amount) {
        if (idempotencyStore.containsKey(idempotencyKey)) {
            return idempotencyStore.get(idempotencyKey) + "  (returned from idempotency store, nothing new created)";
        }
        String id = "ORD-" + (nextOrderId++);
        orders.put(id, new Order(id, amount));
        String response = "201 Created, order: " + orders.get(id);
        idempotencyStore.put(idempotencyKey, response);
        return response;
    }

    // ---------- Level 3: simulate a client retry after a "lost" response ----------
    static void simulateRetryScenario() {
        String key = UUID.randomUUID().toString();
        System.out.println("  client sends POST /orders with Idempotency-Key: " + key);
        String firstAttemptResponse = postWithIdempotencyKey(key, 99.99);
        System.out.println("  server processed it and created a resource, but the response is LOST in transit");
        System.out.println("  (client never saw: " + firstAttemptResponse + ")");
        System.out.println("  client times out, assumes failure, retries with the SAME key:");
        String retryResponse = postWithIdempotencyKey(key, 99.99);
        System.out.println("  " + retryResponse);
        long totalOrdersWithThisAmount = orders.values().stream().filter(o -> o.amount() == 99.99).count();
        System.out.println("  total orders actually created for this purchase: " + totalOrdersWithThisAmount);
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - PUT/DELETE idempotent, plain POST is not:");
        System.out.println("  " + put("5", 20.0));
        System.out.println("  " + put("5", 20.0)); // same call again - same end state
        System.out.println("  " + delete("5"));
        System.out.println("  " + delete("5")); // repeat delete - still "does not exist", no further change
        System.out.println("  " + plainPost(15.0));
        System.out.println("  " + plainPost(15.0) + "  <- SAME logical request, but a SECOND resource was created");

        System.out.println("\nLevel 2 - POST with an idempotency key, called twice with the same key:");
        String key = "key-abc-123";
        System.out.println("  " + postWithIdempotencyKey(key, 50.0));
        System.out.println("  " + postWithIdempotencyKey(key, 50.0));

        System.out.println("\nLevel 3 - full retry scenario, end to end:");
        simulateRetryScenario();
    }
}
```

**How to run:** `java IdempotencyDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `put("5", 20.0)` is called twice in a row with identical arguments. Both calls leave `orders.get("5")` equal to `Order("5", 20.0)` — the second call did real work (it overwrote the entry) but the *end state* is unchanged from after the first call, which is exactly what idempotent means.
2. `delete("5")` is also called twice. The first call finds and removes the order, returning `"200 OK, deleted"`. The second call finds nothing to remove and returns `"404 Not Found"` — the HTTP status code differs, but the state both times afterward is identical: order 5 does not exist.
3. `plainPost(15.0)` is called twice with the same amount. Each call generates a fresh ID (`nextOrderId++`) and creates a **new** `Order` — the output explicitly notes that a second resource was created for what was meant to be one logical request. This is the exact problem idempotency keys solve.
4. **Level 2:** `postWithIdempotencyKey(key, 50.0)` is called twice with the same `key`. The first call finds no entry in `idempotencyStore`, so it creates a new order and stores the response under that key. The second call finds `idempotencyStore.containsKey(key)` true and returns the **stored** response immediately — no new order is created, which the printed output confirms.
5. **Level 3** walks through the realistic failure mode this protects against: the server actually processes the first request and creates an order, but the response is lost before the client sees it — the client cannot tell success from failure. When it retries with the same key, `postWithIdempotencyKey` finds the key already stored and returns the original result. The final count — `totalOrdersWithThisAmount` — confirms exactly one order exists for the $99.99 purchase, despite the client having effectively sent the request twice.

## 7. Gotchas & takeaways

> **Gotcha:** an idempotency key only protects against retries of the *same* logical request. If a client generates a fresh key on every retry (instead of reusing the key from the original attempt), the protection is completely defeated — the key must be generated once, client-side, before the first attempt, and reused on every retry of that same attempt.

- `GET`, `HEAD`, `PUT`, and `DELETE` get idempotency (or safety) for free from their HTTP semantics — design your handlers to actually honor that, since nothing stops a `PUT` handler from behaving non-idempotently if it, say, appends to a list instead of replacing it.
- Add an `Idempotency-Key` header requirement to any `POST` endpoint where a duplicate side effect (a duplicate charge, a duplicate shipment) is a real business risk.
- Store idempotency keys with a bounded expiry window, and document that window to API consumers, so they know how long a retry with the original key remains safe.
- This concern connects directly to [saga](0203-saga-orchestration-vs-choreography.md) compensations and the [transactional outbox](0204-transactional-outbox.md) relay — both patterns rely on at-least-once delivery, which only works correctly if the operations being retried are idempotent.
