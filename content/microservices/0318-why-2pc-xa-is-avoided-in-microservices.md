---
card: microservices
gi: 318
slug: why-2pc-xa-is-avoided-in-microservices
title: "Why 2PC/XA is avoided in microservices"
---

## 1. What it is

**2PC** (two-phase commit) and its standardized implementation **XA** are protocols for making a single transaction span multiple databases atomically — either all participants commit, or all roll back. In a monolith with one database, this need rarely arises. In microservices, where every service owns its own private database, the temptation is to reach for 2PC/XA to keep multi-service updates consistent the way a single-database transaction would be. This topic explains why that temptation is almost always resisted, and a different tool ([the saga pattern](0320-saga-pattern.md)) is used instead.

## 2. Why & when

2PC requires a coordinator to hold locks on every participating database's affected rows for the entire duration of the transaction — from "prepare" until every participant confirms "committed." In a distributed, multi-service system this is disastrous for availability: if any one service is slow, crashed, or network-partitioned during that window, every other participant sits there holding locks, unable to serve any other request touching those rows, for however long it takes to resolve. A single slow or dead participant can stall the entire distributed transaction and, transitively, every other request that needs those locked rows.

It gets worse because 2PC assumes all participants are reachable via a compatible protocol (XA) and that the coordinator itself never permanently dies mid-protocol (a coordinator crash after "prepare" but before broadcasting the final decision leaves participants blocked indefinitely, uncertain whether to commit or roll back). Most microservices deliberately use different, often non-relational, technologies per service (that's [polyglot persistence](0307-polyglot-persistence.md)) — many of which (a message queue, most NoSQL stores) don't even support XA. And most microservice teams explicitly prioritize availability and service independence over cross-service atomicity, which is precisely what 2PC sacrifices.

Use 2PC/XA only in the rare case where you control every participant, they all speak XA, low latency doesn't matter, and a brief system-wide lock is genuinely acceptable — situations that essentially don't exist in an independently-deployed, internet-scale microservices architecture. Otherwise, use the [saga pattern](0320-saga-pattern.md), which achieves eventual consistency without holding cross-service locks.

## 3. Core concept

2PC has two phases: **prepare** (the coordinator asks every participant "can you commit?" and each locks its affected rows and replies yes/no) and **commit** (if all said yes, the coordinator tells everyone to actually commit; if any said no, everyone rolls back). The locks held from "prepare" through "commit" are the core problem — their duration is bounded by the slowest participant and by network round trips, not by any single service's own performance.

```java
// Sketch of the blocking window -- NOT something you'd actually write against
// real XA, just illustrating the shape of the protocol's risk.
interface Participant {
    boolean prepare();   // locks rows, votes yes/no -- LOCKS HELD FROM HERE
    void commit();       // -- UNTIL HERE
    void rollback();
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A coordinator sends prepare to two services which lock rows and reply; the coordinator waits for both before sending commit; if one service is slow, both stay locked the whole time">
  <rect x="250" y="10" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="32" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Coordinator</text>

  <rect x="40" y="90" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="115" y="114" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Order Service (locked)</text>

  <rect x="450" y="90" width="150" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="525" y="110" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Payment Service</text>
  <text x="525" y="123" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="sans-serif">SLOW / locked longer</text>

  <line x1="280" y1="44" x2="150" y2="90" stroke="#8b949e" marker-end="url(#a318)"/>
  <line x1="360" y1="44" x2="500" y2="90" stroke="#8b949e" marker-end="url(#a318)"/>
  <text x="320" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1. prepare (both LOCK rows)</text>

  <text x="320" y="160" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Coordinator WAITS for both -- order-service stays locked the entire time</text>

  <defs><marker id="a318" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every participant locks its rows at "prepare" and cannot release them until the coordinator's final decision arrives — the slowest participant sets the lock duration for everyone.

## 5. Runnable example

Scenario: a simulated two-phase commit across an "order" and "payment" participant, first shown as a straightforward happy path, then extended to show one slow participant blocking the other's lock release, and finally rebuilt as a saga-style approach that avoids holding cross-service locks at all.

### Level 1 — Basic

```java
// File: TwoPhaseCommitHappyPath.java -- simulates the two phases of 2PC
// when both participants are fast and healthy.
public class TwoPhaseCommitHappyPath {
    static boolean orderLocked = false, paymentLocked = false;

    static boolean prepareOrder() { orderLocked = true; System.out.println("order: LOCKED, voting yes"); return true; }
    static boolean preparePayment() { paymentLocked = true; System.out.println("payment: LOCKED, voting yes"); return true; }
    static void commitOrder() { orderLocked = false; System.out.println("order: COMMITTED, lock released"); }
    static void commitPayment() { paymentLocked = false; System.out.println("payment: COMMITTED, lock released"); }

    public static void main(String[] args) {
        System.out.println("Phase 1: PREPARE");
        boolean allYes = prepareOrder() && preparePayment();

        System.out.println("Phase 2: " + (allYes ? "COMMIT" : "ROLLBACK"));
        if (allYes) { commitOrder(); commitPayment(); }
    }
}
```

How to run: `java TwoPhaseCommitHappyPath.java`

Both participants prepare instantly, both vote yes, and both commit and release their locks right away. In this idealized case, the total lock-held time is negligible — but this Level assumes every participant responds instantly, which the next Level shows is not a safe assumption.

### Level 2 — Intermediate

```java
// File: TwoPhaseCommitSlowParticipant.java -- one participant is SLOW to
// prepare; the OTHER participant's lock stays held the whole time it waits.
public class TwoPhaseCommitSlowParticipant {
    static boolean orderLocked = false, paymentLocked = false;

    static boolean prepareOrder() {
        orderLocked = true;
        System.out.println("order: LOCKED at t=0ms, voting yes");
        return true;
    }

    static boolean preparePaymentSlowly() throws InterruptedException {
        System.out.println("payment: starting prepare (simulated SLOW dependency, e.g. a flaky bank API)...");
        Thread.sleep(300); // simulates a slow external call the payment service depends on
        paymentLocked = true;
        System.out.println("payment: LOCKED at t=300ms, voting yes");
        return true;
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        boolean orderVote = prepareOrder(); // order's rows are ALREADY locked here
        boolean paymentVote = preparePaymentSlowly(); // order STAYS locked this whole time

        long blockedMs = System.currentTimeMillis() - start;
        System.out.println("order-service rows were locked for ~" + blockedMs
                + "ms, ENTIRELY because payment-service was slow -- any OTHER request "
                + "needing those order rows had to wait too.");
    }
}
```

How to run: `java TwoPhaseCommitSlowParticipant.java`

`prepareOrder` locks the order rows immediately (`t=0ms`). The coordinator then must also wait for `preparePaymentSlowly`, which sleeps 300ms to simulate a slow dependency. During that entire 300ms, `orderLocked` stays `true` — the order service's rows remain locked purely because of a slowdown in a completely different service. Any other request needing those same order rows would be forced to wait, even though the order service itself was ready to proceed instantly.

### Level 3 — Advanced

```java
// File: SagaInsteadOf2PC.java -- the SAME order+payment scenario, but using
// a saga: each step commits its OWN local transaction immediately (no
// cross-service lock is ever held), and a failure triggers a COMPENSATING
// action instead of a coordinated rollback.
public class SagaInsteadOf2PC {
    static boolean orderPlaced = false, paymentCharged = false;

    static void placeOrder() {
        orderPlaced = true; // commits IMMEDIATELY, locally -- no lock held for anyone else
        System.out.println("order: placed and COMMITTED locally (no cross-service lock held)");
    }

    static boolean chargePayment(boolean simulateFailure) {
        if (simulateFailure) {
            System.out.println("payment: charge FAILED (e.g. card declined)");
            return false;
        }
        paymentCharged = true;
        System.out.println("payment: charged and COMMITTED locally");
        return true;
    }

    static void cancelOrder() { // the COMPENSATING action, run only if payment fails
        orderPlaced = false;
        System.out.println("order: payment failed downstream -- running COMPENSATION: order CANCELLED");
    }

    public static void main(String[] args) {
        placeOrder(); // step 1 commits and releases immediately, no waiting on payment
        boolean paymentOk = chargePayment(true); // simulate a declined card

        if (!paymentOk) cancelOrder(); // compensate instead of rolling back a held lock

        System.out.println("Final state: orderPlaced=" + orderPlaced + ", paymentCharged=" + paymentCharged);
    }
}
```

How to run: `java SagaInsteadOf2PC.java`

`placeOrder` commits its own local change and returns immediately — no lock is held waiting for the payment step. `chargePayment` is then attempted and, in this run, fails (simulating a declined card). Because the order was already committed, there is nothing to "roll back" in the 2PC sense; instead, `cancelOrder` runs as an explicit **compensating transaction** that undoes the order's effect. The final state correctly shows `orderPlaced=false, paymentCharged=false` — consistency was restored through compensation, not through holding locks across both services while waiting for the outcome.

## 6. Walkthrough

Trace `SagaInsteadOf2PC.main` in order. **First**, `placeOrder()` runs and immediately sets `orderPlaced = true` and returns — this is a normal, local, single-service transaction commit; nothing outside the order service is involved or blocked.

**Next**, `chargePayment(true)` runs, passing `true` to simulate a declined card. Inside, the `if (simulateFailure)` branch executes, prints the failure message, and returns `false` without ever setting `paymentCharged`.

**Back in `main`**, `paymentOk` is `false`, so the `if (!paymentOk)` branch runs `cancelOrder()`, which sets `orderPlaced` back to `false` and prints that a compensating cancellation occurred.

**Finally**, `main` prints the final state: `orderPlaced=false, paymentCharged=false` — both services ended up consistent with each other, but this was achieved by each service committing its own transaction immediately and a later step *compensating* for an earlier one's effect, rather than by any cross-service lock ever being held while everyone waited for a single global decision.

```
2PC:   [prepare BOTH (locks held)] -----wait-----> [commit/rollback BOTH]   <- blocking window
Saga:  [commit order] -> [attempt payment: FAILS] -> [compensate: cancel order]  <- no cross-service lock, ever
```

## 7. Gotchas & takeaways

> If a 2PC coordinator crashes after some participants have prepared (locked) but before it broadcasts the final commit/rollback decision, those participants are left "in doubt" — locked indefinitely until the coordinator recovers or an operator intervenes manually. This single failure mode is a major reason distributed-systems teams avoid 2PC across service boundaries.

- 2PC/XA requires holding locks across every participant for the duration of the slowest one — directly opposed to the availability and independence goals of microservices.
- Most microservices deliberately use different data technologies per service ([polyglot persistence](0307-polyglot-persistence.md)); many of those technologies don't support XA at all.
- The alternative is the [saga pattern](0320-saga-pattern.md): each step commits locally and immediately, and failures are undone with explicit compensating actions rather than a coordinated rollback.
- This tradeoff is fundamentally about accepting eventual consistency (see [BASE vs ACID](0327-base-vs-acid.md)) in exchange for availability and service independence.
