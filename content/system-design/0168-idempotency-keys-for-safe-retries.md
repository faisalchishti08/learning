---
card: system-design
gi: 168
slug: idempotency-keys-for-safe-retries
title: Idempotency keys for safe retries
---

## 1. What it is

An **idempotency key** is a unique identifier a client attaches to a request (e.g. `Idempotency-Key: abc-123` header), so that if the same request is sent more than once — due to a retry after a network timeout, for example — the server can recognize it as a duplicate and return the original result instead of performing the operation again. An operation is **idempotent** if performing it multiple times has the exact same effect as performing it once; an idempotency key is how you make a naturally non-idempotent operation (like "charge this card") safe to retry.

## 2. Why & when

A client that sends a "charge $50" request and never receives a response (due to a timeout or a dropped connection) genuinely cannot tell whether the charge succeeded on the server before the response was lost. Retrying blindly risks charging the customer twice; not retrying risks never completing a request that actually failed. An idempotency key solves this: the client generates one key per logical operation (not per network attempt) and sends it with every retry, and the server guarantees it will perform the underlying operation at most once for that key, no matter how many times the request arrives. Use idempotency keys for any operation with a side effect that must not be repeated — payments, order creation, sending a notification — that a client might need to retry after an uncertain failure.

## 3. Core concept

- **Client generates one key per logical operation:** the key is created once, before the first attempt, and reused for every retry of that same logical operation — a new key would defeat the purpose.
- **Server stores the key alongside the operation's result:** on the first request with a given key, the server performs the operation and stores both the key and its result (e.g. in a database with a unique constraint on the key).
- **Duplicate detection:** on a later request with the same key, the server finds the stored result and returns it directly, without repeating the underlying side effect (charging the card again, creating a second order).
- **Concurrent duplicate requests:** if two requests with the same key somehow arrive concurrently (e.g. a client retried while the first attempt was still in flight), the server must ensure only one of them actually performs the operation — often via a unique-constraint insert that only one concurrent request can win.
- **Key expiry:** idempotency keys are usually only stored and honored for a limited window (e.g. 24 hours), after which the same key could theoretically be reused for a genuinely new operation.

## 4. Diagram

```
   client generates key "req-789" ONCE, before the first attempt

   attempt 1: POST /charge  {Idempotency-Key: req-789, amount: 50}
                 |
                 v
        server: key "req-789" not seen before -> charge card -> store (req-789 -> result: charged $50)
                 |
                 v
        response LOST due to network timeout (client never sees it)

   attempt 2 (retry, SAME key): POST /charge  {Idempotency-Key: req-789, amount: 50}
                 |
                 v
        server: key "req-789" already seen -> return STORED result, do NOT charge again
```
*Caption: the server only performs the real side effect on the first request for a given key; every retry with the same key returns the already-computed result instead.*

## 5. Runnable example

**Level 1 — Basic.** Store results keyed by idempotency key, and detect a duplicate on retry.

**Level 2 — Only perform the side effect once per key.** Show the underlying "charge" only actually running a single time despite multiple requests.

**Level 3 — Handle concurrent duplicate requests safely.** Two threads submit the same key at the same time; only one actually performs the charge.

```java
// IdempotencyKeyDemo.java
import java.util.*;
import java.util.concurrent.*;

public class IdempotencyKeyDemo {

    static class ChargeResult {
        final String status;
        final double amount;
        ChargeResult(String status, double amount) { this.status = status; this.amount = amount; }
        public String toString() { return status + " ($" + amount + ")"; }
    }

    // Level 1: stores idempotency key -> result, once computed.
    static final Map<String, ChargeResult> resultsByKey = new ConcurrentHashMap<>();
    static int actualChargeCount = 0; // Level 2: tracks how many times the REAL side effect ran

    // Level 3: computeIfAbsent on a ConcurrentHashMap is atomic per key - only one caller's function runs.
    static ChargeResult chargeCard(String idempotencyKey, double amount) {
        return resultsByKey.computeIfAbsent(idempotencyKey, key -> {
            actualChargeCount++; // this only happens the FIRST time this key is ever seen
            System.out.println("  ACTUALLY CHARGING the card $" + amount + " for key " + key);
            return new ChargeResult("charged", amount);
        });
    }

    public static void main(String[] args) throws InterruptedException {
        String key = "req-789";

        // Level 1 & 2: simulate the original request, then a retry with the SAME key after a lost response.
        System.out.println("attempt 1 (original request):");
        ChargeResult first = chargeCard(key, 50.0);
        System.out.println("  result: " + first);

        System.out.println("attempt 2 (retry after a lost response, SAME key):");
        ChargeResult second = chargeCard(key, 50.0);
        System.out.println("  result: " + second + " (no second charge happened)");

        System.out.println("total actual charges performed: " + actualChargeCount);

        // Level 3: two concurrent retries with the SAME key, racing each other.
        String concurrentKey = "req-999";
        ExecutorService pool = Executors.newFixedThreadPool(2);
        Future<ChargeResult> f1 = pool.submit(() -> chargeCard(concurrentKey, 100.0));
        Future<ChargeResult> f2 = pool.submit(() -> chargeCard(concurrentKey, 100.0));
        System.out.println("concurrent attempt A result: " + f1.get());
        System.out.println("concurrent attempt B result: " + f2.get());
        pool.shutdown();
        System.out.println("total actual charges performed overall: " + actualChargeCount + " (expected 2: one per distinct key)");
    }
}
```

**How to run:** save as `IdempotencyKeyDemo.java`, then run `java IdempotencyKeyDemo.java`.

## 6. Walkthrough

1. `chargeCard(key, 50.0)` calls `resultsByKey.computeIfAbsent(key, ...)`; since `"req-789"` is not yet in the map, the lambda runs, incrementing `actualChargeCount` to 1, printing the "ACTUALLY CHARGING" message, and storing (and returning) the new `ChargeResult`.
2. The second call, `chargeCard(key, 50.0)` with the *same* key, again calls `computeIfAbsent`; this time the key is already present in `resultsByKey`, so the lambda is **not** run at all — no second "ACTUALLY CHARGING" message prints, and the stored `ChargeResult` from the first attempt is returned directly.
3. `actualChargeCount` prints as `1`, confirming the real side effect happened exactly once despite two full "requests" — the second request was recognized purely from its idempotency key and short-circuited before ever reaching the charging logic.
4. For the concurrent case, both `f1` and `f2` call `chargeCard(concurrentKey, 100.0)` at roughly the same time from different threads; `ConcurrentHashMap.computeIfAbsent` guarantees that even under concurrent access, the mapping function runs at most once per key — so only one of the two threads actually executes the lambda and increments `actualChargeCount`.
5. Both `f1.get()` and `f2.get()` return the *same* `ChargeResult` object (whichever thread's computation won), and the final `actualChargeCount` prints as `2` overall — one for `"req-789"` and one for `"req-999"` — confirming that even a genuine race between two duplicate requests for the same key resulted in exactly one real charge, not two.

## 7. Gotchas & takeaways

> Gotcha: storing the idempotency key and performing the side effect as two *separate* steps (check if key exists, then perform the operation, then store the key) reintroduces the exact race this pattern exists to prevent — two concurrent requests could both pass the "check if key exists" step before either has stored anything. The check-and-store (or check-and-perform) must be a single atomic operation, such as a database insert with a unique constraint on the key column, or `computeIfAbsent` as shown here.

- An idempotency key lets a client safely retry an uncertain request without risking the side effect happening more than once.
- The server, not the client, is responsible for deduplicating by key and returning the original result on a repeat.
- The check-and-perform (or check-and-store) step must be atomic, or concurrent duplicate requests can still both slip through.
- Related concepts: [Retries with exponential backoff & jitter](0135-retries-with-exponential-backoff-jitter.md) (what idempotency keys make safe to actually do), [Optimistic vs pessimistic concurrency](0166-optimistic-vs-pessimistic-concurrency.md) (a related but distinct concern: conflicting writes, not duplicate requests), [Saga as an alternative to distributed transactions](0173-saga-as-an-alternative-to-distributed-transactions.md) (idempotent steps are essential to safely retrying a saga step after a failure).
