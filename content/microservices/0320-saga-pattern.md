---
card: microservices
gi: 320
slug: saga-pattern
title: "Saga pattern"
---

## 1. What it is

A **saga** is a sequence of local transactions, one per service, where each local transaction commits immediately and independently, and publishes something (an event or a direct call) that triggers the next step. If any step fails, the saga runs **compensating transactions** to undo the effects of the steps that already succeeded, moving the overall business operation back to a consistent (though not necessarily "as if it never happened") state — without ever holding a lock across services the way [2PC](0319-two-phase-commit-2pc-overview-drawbacks.md) does.

## 2. Why & when

Once every service owns its own private database (see [database per service](0304-database-per-service-pattern.md)), a single business operation that touches several services — "place an order" touching order, payment, and inventory services — can no longer be one ACID transaction. [2PC/XA is avoided in microservices](0318-why-2pc-xa-is-avoided-in-microservices.md) because holding cross-service locks kills availability. The saga pattern is the standard replacement: it accepts that the system will pass through temporarily inconsistent intermediate states (an order marked "placed" before payment is confirmed) in exchange for every step being fast, local, and lock-free.

Use a saga whenever a business process spans multiple services and must eventually reach a consistent outcome, but does not require every intermediate state to be invisible to the rest of the system. It is the default pattern for multi-service writes in microservices; the main design decision is *how* the steps are coordinated — see [choreography-based](0321-choreography-based-saga.md) versus [orchestration-based](0322-orchestration-based-saga.md) sagas.

## 3. Core concept

A saga is a chain: `T1, T2, T3, ..., Tn`, each a local commit in one service. If `Tn` fails, the saga runs compensations for every step that already succeeded, in reverse order: `Cn-1, Cn-2, ..., C1`. Each `Ti` and its corresponding `Ci` are designed together — placing an order (`T1`) is compensated by cancelling it (`C1`); charging a card (`T2`) is compensated by refunding it (`C2`).

```java
record SagaStep(Runnable action, Runnable compensation) {}
// A saga is just an ordered list of these; a failure at step i
// runs compensations for steps i-1, i-2, ..., 0 in reverse.
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three steps run forward: place order, reserve inventory, charge payment; payment fails, so compensations run backward: refund (skipped, nothing charged), release inventory, cancel order">
  <rect x="20" y="20" width="120" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="80" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">T1: place order</text>
  <rect x="180" y="20" width="120" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="240" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">T2: reserve stock</text>
  <rect x="340" y="20" width="130" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="405" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">T3: charge payment</text>
  <text x="405" y="66" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">FAILS</text>

  <line x1="140" y1="37" x2="175" y2="37" stroke="#3fb950" marker-end="url(#a320)"/>
  <line x1="300" y1="37" x2="335" y2="37" stroke="#3fb950" marker-end="url(#a320)"/>

  <rect x="340" y="110" width="130" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="405" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(nothing to undo)</text>
  <rect x="180" y="110" width="120" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="240" y="132" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">C2: release stock</text>
  <rect x="20" y="110" width="120" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="132" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">C1: cancel order</text>

  <line x1="340" y1="127" x2="305" y2="127" stroke="#79c0ff" marker-end="url(#a320b)"/>
  <line x1="180" y1="127" x2="145" y2="127" stroke="#79c0ff" marker-end="url(#a320b)"/>
  <text x="320" y="170" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">compensations run BACKWARD, in reverse order</text>

  <defs>
    <marker id="a320" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a320b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Forward steps commit locally and immediately; a failure triggers compensations for every already-completed step, run in reverse order.

## 5. Runnable example

Scenario: a three-step "place order" saga (order, inventory, payment) that first runs happily to completion, then is extended to fail at the payment step and compensate the earlier steps, and finally hardened so compensations themselves are retried if they fail, since compensations must eventually succeed.

### Level 1 — Basic

```java
// File: SagaHappyPath.java -- three steps, all succeed, no compensation needed.
public class SagaHappyPath {
    static void placeOrder() { System.out.println("T1: order PLACED"); }
    static void reserveStock() { System.out.println("T2: stock RESERVED"); }
    static void chargePayment() { System.out.println("T3: payment CHARGED"); }

    public static void main(String[] args) {
        placeOrder();
        reserveStock();
        chargePayment();
        System.out.println("Saga completed successfully -- no compensation needed.");
    }
}
```

How to run: `java SagaHappyPath.java`

Each step is an independent local commit that runs and returns immediately; there's no cross-service lock and no coordinator waiting on all three at once — each step's success is final the moment it happens.

### Level 2 — Intermediate

```java
// File: SagaWithCompensation.java -- the payment step FAILS; the saga
// compensates the already-completed steps in REVERSE order.
import java.util.*;

public class SagaWithCompensation {
    static List<Runnable> completedCompensations = new ArrayList<>(); // pushed as each step succeeds

    static void placeOrder() {
        System.out.println("T1: order PLACED");
        completedCompensations.add(() -> System.out.println("C1: order CANCELLED"));
    }
    static void reserveStock() {
        System.out.println("T2: stock RESERVED");
        completedCompensations.add(() -> System.out.println("C2: stock RELEASED"));
    }
    static boolean chargePayment() {
        System.out.println("T3: attempting payment charge...");
        System.out.println("T3: payment DECLINED"); // simulated failure
        return false;
    }

    public static void main(String[] args) {
        placeOrder();
        reserveStock();
        boolean paymentOk = chargePayment();

        if (!paymentOk) {
            System.out.println("Saga FAILED at step T3 -- running compensations in REVERSE order:");
            Collections.reverse(completedCompensations); // undo LAST completed step FIRST
            for (Runnable compensation : completedCompensations) compensation.run();
        }
    }
}
```

How to run: `java SagaWithCompensation.java`

As `placeOrder` and `reserveStock` each succeed, they push their own compensation onto `completedCompensations` — this is how the saga remembers what needs undoing without needing a central lock table. When `chargePayment` returns `false`, the saga reverses that list (so the *most recently* completed step is compensated *first*) and runs each compensation: stock is released before the order is cancelled, mirroring the reverse of the order they were created in.

### Level 3 — Advanced

```java
// File: SagaWithRetryingCompensation.java -- a compensation ITSELF can
// fail (e.g. the inventory service is briefly down); this saga retries a
// failing compensation with backoff, because compensations MUST eventually
// succeed or the system is left in a genuinely inconsistent state.
public class SagaWithRetryingCompensation {
    static int releaseStockAttempts = 0;

    static void placeOrder() { System.out.println("T1: order PLACED"); }
    static void reserveStock() { System.out.println("T2: stock RESERVED"); }
    static boolean chargePayment() { System.out.println("T3: payment DECLINED"); return false; }

    static void cancelOrder() { System.out.println("C1: order CANCELLED"); }

    static boolean releaseStock() { // fails the first two attempts, then succeeds -- simulating a flaky dependency
        releaseStockAttempts++;
        if (releaseStockAttempts < 3) {
            System.out.println("C2: release stock attempt " + releaseStockAttempts + " FAILED (inventory service briefly down)");
            return false;
        }
        System.out.println("C2: release stock attempt " + releaseStockAttempts + " SUCCEEDED");
        return true;
    }

    static void runCompensationWithRetry(java.util.function.Supplier<Boolean> compensation, String name) {
        int attempt = 0;
        while (!compensation.get()) { // MUST keep retrying -- compensations are not optional
            attempt++;
            System.out.println("  retrying " + name + " (attempt " + (attempt + 1) + ")...");
        }
    }

    public static void main(String[] args) {
        placeOrder();
        reserveStock();
        boolean paymentOk = chargePayment();

        if (!paymentOk) {
            System.out.println("Saga FAILED -- compensating in reverse order:");
            runCompensationWithRetry(SagaWithRetryingCompensation::releaseStock, "release-stock"); // C2 first
            cancelOrder(); // C1 second
            System.out.println("All compensations completed -- system is consistent again.");
        }
    }
}
```

How to run: `java SagaWithRetryingCompensation.java`

`releaseStock` is written to fail on its first two calls and succeed on the third, standing in for a real, transient outage in the inventory service. `runCompensationWithRetry` calls it in a loop, retrying every time it returns `false`, and only proceeds to `cancelOrder` once `releaseStock` finally returns `true`. This matters because a saga's compensations are not optional cleanup — if `releaseStock` simply failed once and the saga moved on, stock would remain incorrectly reserved forever; compensations must be retried (often indefinitely, sometimes escalated to a human) until they succeed.

## 6. Walkthrough

Trace `SagaWithRetryingCompensation.main` in order. **First**, `placeOrder()` and `reserveStock()` run, each printing that its local transaction committed — `T1` and `T2` are now durably done, independently, in their own services.

**Next**, `chargePayment()` runs and returns `false`, representing a declined card. Because `paymentOk` is `false`, the `if` branch begins compensating.

**`runCompensationWithRetry` is called first, for `releaseStock`** (compensating `T2`, the most recently completed step). Internally, its `while` loop calls `releaseStock()` repeatedly: the first call increments `releaseStockAttempts` to `1` and returns `false` (printed as attempt 1 failing); the loop retries, the second call increments to `2` and again returns `false`; the loop retries again, the third call increments to `3`, this time the `if (releaseStockAttempts < 3)` guard is false, so it prints success and returns `true`, which ends the `while` loop.

**Then**, `cancelOrder()` runs (compensating `T1`), printing that the order was cancelled — this always succeeds in this example, but in a real system it would use the same retry pattern if it could also fail transiently.

**Finally**, `main` prints that all compensations completed. The net effect: order placed then cancelled, stock reserved then released (after retries), payment never actually charged — the three services are left mutually consistent, even though nothing was ever locked across them while payment was being attempted.

```
T1 place-order (commit) -> T2 reserve-stock (commit) -> T3 charge-payment: FAILS
                                                              |
                                    compensate T2 first: release-stock (fails, fails, succeeds)
                                                              |
                                              compensate T1: cancel-order (succeeds)
```

## 7. Gotchas & takeaways

> A saga does not undo history the way a database rollback does — the order genuinely *was* placed and then cancelled; anyone who observed the intermediate "placed" state (an email confirmation, a dashboard) saw a real, if temporary, state. Compensating transactions must be designed to be visible-safe, since the intermediate state was never hidden the way a 2PC transaction's uncommitted state would be.

- Every forward step and its compensation are designed as a pair; a step that cannot be meaningfully undone (like sending an email) needs a different strategy, such as delaying it until the saga is known to succeed.
- Compensations run in reverse order of the steps that completed, and must themselves be retried until they succeed — a failed compensation is a genuinely inconsistent system, not just a failed request.
- Sagas trade strict cross-service atomicity for availability: see [why 2PC/XA is avoided in microservices](0318-why-2pc-xa-is-avoided-in-microservices.md) and [BASE vs ACID](0327-base-vs-acid.md).
- The two main ways to coordinate a saga's steps are [choreography](0321-choreography-based-saga.md) (services react to each other's events, no central coordinator) and [orchestration](0322-orchestration-based-saga.md) (a central orchestrator tells each service what to do next).
