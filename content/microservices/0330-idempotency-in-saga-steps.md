---
card: microservices
gi: 330
slug: idempotency-in-saga-steps
title: "Idempotency in saga steps"
---

## 1. What it is

**Idempotency** in a saga step means that executing the same step more than once with the same input produces the same result as executing it exactly once — no double charge, no double stock decrement, no duplicate order. Every step (and every compensation) in a [saga](0320-saga-pattern.md) needs this property, because sagas run over unreliable networks and messaging systems that typically guarantee at-least-once delivery, meaning any given step's trigger can arrive, and be acted on, more than once.

## 2. Why & when

A saga step is usually triggered by a message — an event in a [choreography-based saga](0321-choreography-based-saga.md), or a command from an orchestrator. Messaging systems that guarantee at-least-once delivery (most of them) will, on occasion, deliver the same message twice: a consumer processes a message but crashes before acknowledging it, so the broker redelivers it; a network blip causes a retry that duplicates an already-successful call. If a step isn't idempotent, this ordinary occurrence becomes a real bug — a customer charged twice, inventory decremented twice for one order.

Make every saga step and every compensation idempotent as a baseline requirement, not an edge case to handle "if it comes up." This applies universally across both choreography and orchestration styles, and to every messaging technology, since at-least-once delivery is the norm, not the exception, in distributed messaging.

## 3. Core concept

The standard technique is to give every action a unique, stable identifier (an idempotency key — often the same ID as the triggering event) and record, durably, which keys have already been processed. Before performing the action's real side effect, the step checks whether its key has already been seen; if so, it skips the side effect and returns the previously recorded result instead of redoing the work.

```java
record IdempotencyRecord(String key, String result) {} // one row per (attempted) action, keyed uniquely
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A charge-payment message is delivered twice with the same idempotency key; the first delivery performs the charge and records the key; the second delivery finds the key already recorded and skips the charge, returning the same result">
  <rect x="20" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Delivery 1: key=evt-7</text>
  <rect x="20" y="90" width="180" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="110" y="112" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Delivery 2: key=evt-7</text>

  <line x1="200" y1="37" x2="290" y2="37" stroke="#3fb950" marker-end="url(#a330)"/>
  <rect x="300" y="20" width="160" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="380" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">CHARGE performed, key stored</text>

  <line x1="200" y1="107" x2="290" y2="107" stroke="#79c0ff" marker-end="url(#a330b)"/>
  <rect x="300" y="90" width="160" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="380" y="112" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">key FOUND -&gt; SKIP, return same result</text>

  <defs>
    <marker id="a330" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a330b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The first delivery of a given key performs the real action and records it; every subsequent delivery of the same key is recognized and skipped.

## 5. Runnable example

Scenario: a payment-charging saga step that double-charges on redelivery, then fixed with an idempotency key check, then extended to handle the trickier case of a duplicate arriving *while the first attempt is still in progress*, not just after it completed.

### Level 1 — Basic

```java
// File: NonIdempotentChargeStep.java -- the saga step has NO idempotency
// check; a redelivered message charges the card TWICE.
import java.util.*;

public class NonIdempotentChargeStep {
    static Map<String, Double> totalCharged = new HashMap<>();

    static void chargePaymentStep(String orderId, double amount) {
        totalCharged.merge(orderId, amount, Double::sum); // blindly adds, EVERY time called
        System.out.println("charged $" + amount + " for " + orderId + " -- running total: $" + totalCharged.get(orderId));
    }

    public static void main(String[] args) {
        chargePaymentStep("order-1", 50.0); // first delivery
        chargePaymentStep("order-1", 50.0); // REDELIVERY of the SAME logical charge
        System.out.println("Final total charged: $" + totalCharged.get("order-1") + " -- should be $50, customer was DOUBLE-CHARGED!");
    }
}
```

How to run: `java NonIdempotentChargeStep.java`

`chargePaymentStep` has no way to recognize the second call is a redelivery of the same logical event, so it adds `50.0` twice, leaving `totalCharged` at `$100.0` for a purchase that should have cost `$50.0`.

### Level 2 — Intermediate

```java
// File: IdempotentChargeStep.java -- an idempotency key (the triggering
// event's own ID) is tracked; a redelivered message is recognized and SKIPPED.
import java.util.*;

public class IdempotentChargeStep {
    static Map<String, Double> totalCharged = new HashMap<>();
    static Set<String> processedEventIds = new HashSet<>();

    static void chargePaymentStep(String orderId, double amount, String eventId) {
        if (!processedEventIds.add(eventId)) { // add() returns false if ALREADY present
            System.out.println("event " + eventId + " already processed -- SKIPPING duplicate charge");
            return;
        }
        totalCharged.merge(orderId, amount, Double::sum);
        System.out.println("charged $" + amount + " for " + orderId + " (event " + eventId + ") -- running total: $" + totalCharged.get(orderId));
    }

    public static void main(String[] args) {
        chargePaymentStep("order-1", 50.0, "evt-7"); // first delivery
        chargePaymentStep("order-1", 50.0, "evt-7"); // REDELIVERY, same eventId
        System.out.println("Final total charged: $" + totalCharged.get("order-1") + " -- correct, DESPITE the redelivery.");
    }
}
```

How to run: `java IdempotentChargeStep.java`

`processedEventIds.add("evt-7")` returns `true` the first time (newly inserted) and `false` the second time (already present), which the code uses to skip the redelivered charge entirely. The final total correctly stays at `$50.0`, matching the single logical charge that should have occurred.

### Level 3 — Advanced

```java
// File: IdempotentChargeInFlightSafe.java -- handles the HARDER case: a
// duplicate arrives WHILE the first attempt is still being processed (not
// yet marked complete), which a simple Set.add() check alone does not
// safely cover if the first attempt hasn't finished recording its result.
import java.util.*;

public class IdempotentChargeInFlightSafe {
    enum Status { IN_PROGRESS, COMPLETED }
    record ChargeRecord(Status status, Double resultAmount) {}
    static Map<String, ChargeRecord> chargeRecords = new HashMap<>(); // keyed by eventId
    static Map<String, Double> totalCharged = new HashMap<>();

    static Double chargePaymentStep(String orderId, double amount, String eventId) {
        ChargeRecord existing = chargeRecords.get(eventId);
        if (existing != null) {
            if (existing.status() == Status.IN_PROGRESS) {
                System.out.println("event " + eventId + " is ALREADY IN PROGRESS -- refusing to start a SECOND concurrent attempt");
                return null; // caller should retry later, NOT proceed with a second real charge
            }
            System.out.println("event " + eventId + " already COMPLETED -- returning the SAME recorded result: $" + existing.resultAmount());
            return existing.resultAmount();
        }

        chargeRecords.put(eventId, new ChargeRecord(Status.IN_PROGRESS, null)); // claim it BEFORE doing the real work
        totalCharged.merge(orderId, amount, Double::sum);
        chargeRecords.put(eventId, new ChargeRecord(Status.COMPLETED, amount)); // mark done, remembering the result
        System.out.println("charged $" + amount + " for " + orderId + " (event " + eventId + ") -- running total: $" + totalCharged.get(orderId));
        return amount;
    }

    public static void main(String[] args) {
        chargePaymentStep("order-1", 50.0, "evt-7"); // completes normally

        Double duplicateAfterCompletion = chargePaymentStep("order-1", 50.0, "evt-7"); // duplicate AFTER completion
        System.out.println("duplicate-after-completion returned: $" + duplicateAfterCompletion + " -- same result, no new charge.");

        // Simulate a duplicate arriving mid-flight, before the first attempt marked itself COMPLETED.
        chargeRecords.put("evt-9", new ChargeRecord(Status.IN_PROGRESS, null)); // manually simulate "already claimed, not yet done"
        Double duringInFlight = chargePaymentStep("order-1", 25.0, "evt-9");
        System.out.println("duplicate-while-in-flight returned: " + duringInFlight + " -- correctly refused a SECOND concurrent charge attempt.");

        System.out.println("Final total charged for order-1: $" + totalCharged.get("order-1"));
    }
}
```

How to run: `java IdempotentChargeInFlightSafe.java`

The first call for `evt-7` finds no existing record, claims it as `IN_PROGRESS` *before* performing the charge, then updates it to `COMPLETED` with the result. The second call for the same `evt-7`, run after completion, finds the `COMPLETED` record and returns the same `$50.0` without charging again. The third call uses `evt-9`, manually pre-seeded as `IN_PROGRESS` to simulate a duplicate arriving *while* the original attempt for that event is still mid-flight (not yet marked done) — the method correctly refuses to start a second real charge in that window too, returning `null` so the caller knows to retry later rather than risk a double charge racing with the still-in-progress original.

## 6. Walkthrough

Trace `IdempotentChargeInFlightSafe.main` in order. **First**, `chargePaymentStep("order-1", 50.0, "evt-7")` runs: `chargeRecords.get("evt-7")` is `null`, so it claims the key with `IN_PROGRESS`, performs the charge (`totalCharged` becomes `50.0`), then overwrites the record with `COMPLETED` and `resultAmount=50.0`.

**Next**, the same call is repeated for `"evt-7"`. This time `existing` is the `COMPLETED` record from before; since its status is not `IN_PROGRESS`, the method takes the "already completed" branch, printing and returning the stored `resultAmount` of `50.0` — no new charge happens.

**Then**, the test manually inserts `chargeRecords.put("evt-9", new ChargeRecord(IN_PROGRESS, null))`, simulating a scenario where a first attempt for `evt-9` has already claimed the key but not yet finished. `chargePaymentStep` is called for `evt-9`: `existing` is found and its status *is* `IN_PROGRESS`, so the method takes the "already in progress" branch, printing a refusal message and returning `null` — critically, it does **not** proceed to charge, because doing so here would race with whatever original attempt is still mid-flight for that same event.

**Finally**, `main` prints the total charged for `order-1`, which is `$50.0` — exactly one real charge occurred, across three calls that included both a straightforward redelivery and a trickier in-flight-duplicate scenario.

```
chargePaymentStep(evt-7) #1  -> no record -> claim IN_PROGRESS -> charge -> mark COMPLETED($50)
chargePaymentStep(evt-7) #2  -> record COMPLETED -> return $50, NO new charge
chargePaymentStep(evt-9)     -> record IN_PROGRESS (pre-seeded) -> REFUSE, return null, NO charge
```

## 7. Gotchas & takeaways

> A `Set` of processed IDs, checked and added in two separate steps, has a subtle gap: if a duplicate arrives after the ID is added but before the real side effect (like the actual charge) completes, a naive check can still allow two charges to race. Claiming the key (marking it `IN_PROGRESS`) *before* doing the real work, as in Level 3, closes this gap.

- Every saga step and compensation must be idempotent, keyed by a stable identifier from the triggering message — this is a baseline requirement, not an edge case.
- A simple "already processed" set works for the common case of a duplicate arriving *after* the first attempt completed; a duplicate arriving *during* the first attempt needs an explicit in-progress state to avoid a race.
- This same idempotency discipline underlies the [inbox pattern](0339-inbox-pattern-for-idempotent-consumption.md) for consuming events safely, and pairs with the [transactional outbox pattern](0331-transactional-outbox-pattern.md) on the publishing side.
- Idempotency keys are typically the event's own unique ID, not a value derived from the business data alone, since the same business operation might legitimately be retried by a user later with a *new* key.
