---
card: microservices
gi: 507
slug: idempotency-keys
title: "Idempotency keys"
---

## 1. What it is

An **idempotency key** is a unique identifier the client generates and attaches to a request (typically as a header, `Idempotency-Key: abc-123`) so the server can recognize and safely handle a **retried** request as the *same* operation rather than a *new* one. If the server has already processed a request with that exact key, it returns the original result again without re-executing the underlying operation — making an operation that isn't naturally idempotent (like "charge this card") safe to retry.

## 2. Why & when

You need idempotency keys whenever a client might retry a request whose underlying operation has a side effect that shouldn't happen twice:

- **Network failures are ambiguous about what actually happened.** If a client sends a "charge $50" request and the connection drops before the response arrives, the client genuinely doesn't know whether the charge succeeded or failed — retrying is the only reasonable option, but retrying a naturally non-idempotent operation risks charging the customer twice.
- **[Retries](0481-mesh-level-resiliency-retries-timeouts-circuit-breaking.md) at any layer — client code, a mesh proxy, a resiliency library — assume it's safe to resend a request.** That assumption is only actually safe for operations that are either naturally idempotent (a `GET`, a `PUT` that sets an absolute value) or explicitly made idempotent via a key like this.
- **The server, not the client, must be the one enforcing the deduplication**, since the whole point is protecting against the client's own retry behavior — a client-side "don't send this twice" check does nothing if the client itself doesn't know whether its first attempt actually landed.
- **You add idempotency key support to any endpoint that creates a side effect that would be harmful if duplicated** — payments, order creation, sending a notification — essentially any `POST` or non-idempotent operation with a real-world consequence to duplication.

## 3. Core concept

Think of a claim ticket at a dry cleaner: you're given a unique ticket number when you drop off clothes, and if you come back and hand over the same ticket number again, they recognize it and hand you the same clothes rather than treating it as a brand-new drop-off. The ticket number is what lets the dry cleaner distinguish "the same transaction, mentioned again" from "a genuinely new transaction," even if you show up and ask twice.

Concretely:

1. **The client generates a unique key** (typically a UUID) for each logically distinct operation, before making the request — the same key must be reused on any retry of that exact same logical operation.
2. **The client sends the key with the request**, usually as a header.
3. **The server checks whether it has already processed this key.** If not, it performs the operation, stores the key alongside the result, and returns the result normally.
4. **If the key has been seen before, the server returns the stored result from the original processing**, without re-executing the operation's side effects — the retry is safe precisely because the server recognizes it as a duplicate of something already done.
5. **Keys are typically stored with a reasonable expiration** — long enough to cover realistic retry windows, short enough not to accumulate unbounded storage for keys that will never be retried again.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client's original request is processed and its result stored under the idempotency key; a retry with the same key returns the stored result without re-executing the operation">
  <rect x="20" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">original request, key=abc-123</text>
  <text x="160" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">EXECUTES the charge, stores result</text>

  <rect x="360" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="500" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">retry, SAME key=abc-123</text>
  <text x="500" y="65" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">returns STORED result, no re-charge</text>

  <text x="330" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">both requests, same key, receive the SAME response -- but the charge only happens ONCE</text>
</svg>

The retry, carrying the identical key, receives the original stored result instead of triggering a duplicate charge.

## 5. Runnable example

Scenario: a payment endpoint using idempotency keys. We start with a basic version demonstrating a naive endpoint charging twice on retry (the problem), extend it to idempotency-key-protected deduplication, then handle the hard case: two genuinely concurrent requests with the same key racing each other, which must still result in exactly one charge, not a race condition that lets both through.

### Level 1 — Basic

```java
// File: NoIdempotencyProblem.java -- models the PROBLEM: a payment
// endpoint with NO idempotency protection. A network retry causes the
// SAME logical charge to be processed TWICE.
import java.util.concurrent.atomic.*;

public class NoIdempotencyProblem {
    static AtomicInteger totalChargesProcessed = new AtomicInteger(0);

    static String chargeCard(String customerId, double amount) {
        int chargeNumber = totalChargesProcessed.incrementAndGet();
        System.out.println("[payment] CHARGED customer " + customerId + " $" + amount + " (charge #" + chargeNumber + ")");
        return "charge-" + chargeNumber;
    }

    public static void main(String[] args) {
        // Client sends a request, network drops the RESPONSE (not the request), client retries.
        System.out.println("[client] sending charge request");
        chargeCard("cust-42", 50.00);

        System.out.println("[client] no response received (network issue) -- RETRYING the same logical request");
        chargeCard("cust-42", 50.00); // SAME logical operation, but the server has no way to know that

        System.out.println("[result] customer was charged " + totalChargesProcessed.get() + " times for what should have been ONE $50 charge");
    }
}
```

How to run: `java NoIdempotencyProblem.java`

`chargeCard` has no concept of "have I seen this operation before" — it simply executes and increments `totalChargesProcessed` every time it's called, so the client's retry, indistinguishable from a genuinely new charge request as far as the server is concerned, results in the customer being charged twice for one intended transaction.

### Level 2 — Intermediate

```java
// File: IdempotencyKeyBasic.java -- the SAME payment flow, now PROTECTED
// with an idempotency key: the server recognizes a RETRY (same key) and
// returns the ORIGINAL result instead of charging again.
import java.util.*;
import java.util.concurrent.atomic.*;

public class IdempotencyKeyBasic {
    static AtomicInteger totalChargesProcessed = new AtomicInteger(0);
    static Map<String, String> processedKeys = new HashMap<>(); // idempotency key -> result

    static String chargeCardIdempotent(String idempotencyKey, String customerId, double amount) {
        if (processedKeys.containsKey(idempotencyKey)) {
            String cachedResult = processedKeys.get(idempotencyKey);
            System.out.println("[payment] key '" + idempotencyKey + "' ALREADY PROCESSED -- returning stored result, NOT re-charging");
            return cachedResult;
        }
        int chargeNumber = totalChargesProcessed.incrementAndGet();
        String result = "charge-" + chargeNumber;
        System.out.println("[payment] CHARGED customer " + customerId + " $" + amount + " (charge #" + chargeNumber + "), key='" + idempotencyKey + "'");
        processedKeys.put(idempotencyKey, result);
        return result;
    }

    public static void main(String[] args) {
        String idempotencyKey = "req-9f8e7d6c"; // generated ONCE by the client for this logical operation

        System.out.println("[client] sending charge request with key " + idempotencyKey);
        String result1 = chargeCardIdempotent(idempotencyKey, "cust-42", 50.00);

        System.out.println("[client] no response received -- RETRYING with the SAME key");
        String result2 = chargeCardIdempotent(idempotencyKey, "cust-42", 50.00);

        System.out.println("[result] both calls returned: " + result1 + " and " + result2 + " -- customer charged " + totalChargesProcessed.get() + " time(s)");
    }
}
```

How to run: `java IdempotencyKeyBasic.java`

`processedKeys` maps each idempotency key to the result it produced the first time it was processed. The second call, using the identical `idempotencyKey`, finds it already present via `containsKey`, so it returns the cached `result` directly without incrementing `totalChargesProcessed` again — the customer is charged exactly once, and both the original request and its retry receive the same, correct result.

### Level 3 — Advanced

```java
// File: IdempotencyKeyConcurrentRace.java -- the SAME key-based
// deduplication, now handling the PRODUCTION-FLAVORED hard case: TWO
// requests carrying the SAME idempotency key arrive nearly
// SIMULTANEOUSLY, genuinely concurrently -- a real possibility if a
// client's retry logic fires before the first attempt's response even
// returns. A NAIVE check-then-act (check processedKeys, THEN charge) has
// a RACE CONDITION that can let BOTH through. This must be made properly
// ATOMIC.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class IdempotencyKeyConcurrentRace {
    static AtomicInteger totalChargesProcessed = new AtomicInteger(0);
    static ConcurrentHashMap<String, CompletableFuture<String>> inFlightOrCompleted = new ConcurrentHashMap<>();

    static String actuallyChargeCard(String customerId, double amount) {
        int chargeNumber = totalChargesProcessed.incrementAndGet();
        try { Thread.sleep(30); } catch (InterruptedException ignored) {} // simulates real processing time
        System.out.println("[payment] CHARGED customer " + customerId + " $" + amount + " (charge #" + chargeNumber + ")");
        return "charge-" + chargeNumber;
    }

    static String chargeCardIdempotentAtomic(String idempotencyKey, String customerId, double amount) {
        // computeIfAbsent is ATOMIC per key -- only ONE caller's supplier actually runs,
        // even under genuine concurrent access to the same key.
        CompletableFuture<String> future = inFlightOrCompleted.computeIfAbsent(idempotencyKey, k ->
            CompletableFuture.supplyAsync(() -> actuallyChargeCard(customerId, amount))
        );
        try {
            return future.get();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        String sharedIdempotencyKey = "req-race-condition-test";
        int concurrentRetries = 10;

        ExecutorService pool = Executors.newFixedThreadPool(concurrentRetries);
        CountDownLatch latch = new CountDownLatch(concurrentRetries);

        for (int i = 0; i < concurrentRetries; i++) {
            pool.submit(() -> {
                chargeCardIdempotentAtomic(sharedIdempotencyKey, "cust-42", 50.00);
                latch.countDown();
            });
        }
        latch.await();
        pool.shutdown();

        System.out.println("[result] " + concurrentRetries + " GENUINELY CONCURRENT requests, same key -- customer charged "
                + totalChargesProcessed.get() + " time(s) total");
    }
}
```

How to run: `java IdempotencyKeyConcurrentRace.java`

`ConcurrentHashMap.computeIfAbsent` guarantees that for any given key, its supplier function runs *at most once*, even when called concurrently from multiple threads — this is the atomicity a naive "check `containsKey`, then separately call `put`" approach lacks, since two threads could both pass the check before either calls `put`. All ten concurrent threads calling `chargeCardIdempotentAtomic` with the identical key end up sharing exactly one `CompletableFuture`, and therefore exactly one actual call to `actuallyChargeCard`.

## 6. Walkthrough

Trace `IdempotencyKeyConcurrentRace.main` in order. **First**, ten threads are submitted to the pool nearly simultaneously, each calling `chargeCardIdempotentAtomic` with the identical `sharedIdempotencyKey`.

**Next**, all ten threads race to call `inFlightOrCompleted.computeIfAbsent(sharedIdempotencyKey, ...)` at roughly the same time. `ConcurrentHashMap`'s `computeIfAbsent` is internally synchronized per key — only one thread's call actually executes the supplier lambda (which calls `actuallyChargeCard`), while every other thread's call to `computeIfAbsent` for that same key blocks briefly and then receives the *same* `CompletableFuture` reference the winning thread created, without running the supplier itself.

**Then**, the one thread that won the race executes `actuallyChargeCard`, which increments `totalChargesProcessed` to `1`, sleeps briefly to simulate real processing, prints the charge confirmation, and returns the result — completing the shared `CompletableFuture`.

**After that**, every one of the other nine threads calls `.get()` on that same completed future, receiving the identical result the moment it's available, without any of them ever having called `actuallyChargeCard` themselves.

**Finally**, `main` prints the total: `totalChargesProcessed.get()` equals exactly `1`, despite ten genuinely concurrent requests all carrying the same idempotency key — demonstrating that the atomicity of `computeIfAbsent` closes the race-condition window a naive check-then-act approach would have left open, where two threads could both observe "not yet processed" before either one finished processing.

```
[payment] CHARGED customer cust-42 $50.0 (charge #1)
[result] 10 GENUINELY CONCURRENT requests, same key -- customer charged 1 time(s) total
```

## 7. Gotchas & takeaways

> A naive idempotency implementation — checking `if (!processedKeys.containsKey(key))` and then separately calling `processedKeys.put(key, result)` afterward — has a genuine race condition: two concurrent requests can both pass the `containsKey` check before either one completes its `put`, resulting in the operation executing twice despite an idempotency key being present. Always use an atomic check-and-set primitive (`computeIfAbsent`, a database's `INSERT ... ON CONFLICT`, a distributed lock) rather than separate check-then-act steps.
- Idempotency keys should be generated by the *client*, once per logical operation, and explicitly reused on any retry of that same operation — a new key on every retry attempt defeats the entire purpose.
- Store idempotency keys with a reasonable expiration (hours to days, depending on realistic retry windows) — keeping them forever accumulates unbounded storage, while expiring them too quickly risks a legitimate late retry being treated as a brand-new operation.
- This pattern is what makes it *safe* to layer [mesh-level or library-based retries](0481-mesh-level-resiliency-retries-timeouts-circuit-breaking.md) on top of otherwise non-idempotent operations — without an idempotency key, blindly retrying a payment or order-creation call is genuinely dangerous, not just theoretically imperfect.
- Return the exact same response (status code and body) for a deduplicated retry as for the original request — a client's retry logic generally expects a consistent, predictable response shape regardless of whether its request was the original or a recognized duplicate.
