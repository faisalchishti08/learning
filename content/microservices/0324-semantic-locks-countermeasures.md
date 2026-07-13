---
card: microservices
gi: 324
slug: semantic-locks-countermeasures
title: "Semantic locks & countermeasures"
---

## 1. What it is

A **semantic lock** is an application-level flag on a record — a status field like `PENDING`, `RESERVED`, or `IN_PROGRESS` — that marks the record as being in the middle of a [saga](0320-saga-pattern.md), so other operations can recognize it is not yet in a final, trustworthy state and behave differently around it. Because sagas can't use real database locks across services (that's exactly what [2PC](0319-two-phase-commit-2pc-overview-drawbacks.md) does, and sagas exist to avoid it), a semantic lock is the substitute: a visible marker, checked by application code, instead of a row lock enforced by a database engine.

## 2. Why & when

Between a saga's forward steps, the affected records are visible to everyone — there is no cross-service lock hiding the "order placed, payment not yet confirmed" state. Left unmarked, this creates real problems: another process might try to cancel an order that's mid-saga, or count an unconfirmed reservation as sold-out inventory, or let a second, unrelated saga read and act on data that is about to be compensated away. A semantic lock exists to make that in-progress state explicit and checkable, so other code paths can apply their own countermeasures — refuse the conflicting action, queue it, or reinterpret the data appropriately — instead of naively treating a mid-saga record as finished.

Use a semantic lock whenever a saga's intermediate states are visible to other operations that could be misled by them, which in practice is almost every saga touching shared, queryable data. Skip it only for steps whose intermediate state genuinely can't cause a problem if observed or acted upon by something else.

## 3. Core concept

A record gets a status field that transitions through the saga: `PENDING` while a step is in flight, a terminal state (`CONFIRMED`, `CANCELLED`) once the saga finishes one way or the other. Other code paths that read or act on that record are written to check the status and apply the appropriate countermeasure — commonly one of: **reread** (re-fetch and recheck before acting), **commutative updates** (design operations so order doesn't matter, sidestepping the conflict), or **pessimistic view** (treat a `PENDING` record as not-yet-actionable and reject or queue the conflicting operation).

```java
enum ReservationStatus { PENDING, CONFIRMED, CANCELLED } // the semantic lock IS this field
record StockReservation(String orderId, int quantity, ReservationStatus status) {}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stock reservation moves from PENDING to CONFIRMED or CANCELLED; while PENDING, a countermeasure rejects a conflicting cancellation request instead of blindly acting on a record that is still mid-saga">
  <rect x="30" y="60" width="140" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="100" y="84" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">status: PENDING</text>

  <rect x="250" y="10" width="150" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="325" y="34" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">status: CONFIRMED</text>
  <rect x="250" y="110" width="150" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="325" y="134" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">status: CANCELLED</text>

  <line x1="170" y1="70" x2="245" y2="35" stroke="#3fb950" marker-end="url(#a324)"/>
  <line x1="170" y1="90" x2="245" y2="120" stroke="#f85149" marker-end="url(#a324)"/>

  <rect x="440" y="55" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Other request sees PENDING</text>
  <text x="530" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-&gt; rejected / queued</text>
  <line x1="170" y1="80" x2="435" y2="80" stroke="#79c0ff" stroke-dasharray="3,3" marker-end="url(#a324b)"/>

  <defs>
    <marker id="a324" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a324b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The status field is the semantic lock; other operations check it and apply a countermeasure instead of acting on a still-in-flight record.

## 5. Runnable example

Scenario: a stock reservation that, unmarked, lets a conflicting cancellation corrupt state mid-saga, then fixed with a `PENDING` semantic lock that rejects the conflict, and finally extended to a reread-based countermeasure that lets the conflicting request retry once the saga resolves instead of failing outright.

### Level 1 — Basic

```java
// File: NoSemanticLock.java -- a reservation has NO status field; a
// conflicting cancellation request can act on it mid-saga, corrupting state.
import java.util.*;

public class NoSemanticLock {
    static Map<String, Integer> stockReserved = new HashMap<>();

    static void reserveStock(String orderId, int qty) {
        stockReserved.put(orderId, qty);
        System.out.println("inventory: reserved " + qty + " units for " + orderId + " (saga step 1 of 2, payment not yet confirmed)");
    }

    static void cancelReservationIfNoPendingOrder(String orderId) { // a DIFFERENT process, unaware of the in-flight saga
        stockReserved.remove(orderId); // WRONG: acts on a reservation that's still mid-saga
        System.out.println("cleanup job: removed reservation for " + orderId + " -- but the saga wasn't done yet!");
    }

    public static void main(String[] args) {
        reserveStock("order-1", 5);
        cancelReservationIfNoPendingOrder("order-1"); // races with the in-flight saga, corrupting it
        System.out.println("Final state: " + stockReserved + " -- reservation LOST while payment was still being processed.");
    }
}
```

How to run: `java NoSemanticLock.java`

With no status field, `cancelReservationIfNoPendingOrder` has no way to know the reservation is mid-saga (payment hasn't been confirmed yet) versus abandoned. It simply removes it, corrupting the in-flight saga's state — the payment step, whenever it runs, will find the reservation gone.

### Level 2 — Intermediate

```java
// File: SemanticLockRejects.java -- adds a status field (the semantic
// lock); the conflicting operation now CHECKS it and REJECTS the conflict
// instead of blindly acting.
import java.util.*;

public class SemanticLockRejects {
    enum Status { PENDING, CONFIRMED, CANCELLED }
    record Reservation(String orderId, int qty, Status status) {}
    static Map<String, Reservation> reservations = new HashMap<>();

    static void reserveStock(String orderId, int qty) {
        reservations.put(orderId, new Reservation(orderId, qty, Status.PENDING)); // semantic lock: PENDING
        System.out.println("inventory: reserved " + qty + " units for " + orderId + ", status=PENDING");
    }

    static void confirmReservation(String orderId) {
        Reservation r = reservations.get(orderId);
        reservations.put(orderId, new Reservation(orderId, r.qty(), Status.CONFIRMED));
        System.out.println("inventory: reservation for " + orderId + " CONFIRMED (payment succeeded)");
    }

    static boolean tryCancelReservation(String orderId) { // the COUNTERMEASURE: checks the semantic lock first
        Reservation r = reservations.get(orderId);
        if (r.status() == Status.PENDING) {
            System.out.println("cleanup job: reservation for " + orderId + " is PENDING (mid-saga) -- REJECTING cancellation");
            return false;
        }
        reservations.remove(orderId);
        return true;
    }

    public static void main(String[] args) {
        reserveStock("order-1", 5);
        boolean cancelled = tryCancelReservation("order-1"); // correctly rejected -- saga still in flight
        System.out.println("Cancellation attempt succeeded? " + cancelled);

        confirmReservation("order-1"); // the saga's payment step finishes normally
        System.out.println("Final reservation: " + reservations.get("order-1"));
    }
}
```

How to run: `java SemanticLockRejects.java`

`tryCancelReservation` now checks `r.status()` before acting. Because the reservation is still `PENDING`, the conflicting cancellation is rejected outright, printed clearly as a deliberate decision rather than a silent corruption. The saga is then free to proceed normally: `confirmReservation` transitions the status to `CONFIRMED`, and the reservation survives intact.

### Level 3 — Advanced

```java
// File: SemanticLockWithReread.java -- instead of permanently REJECTING a
// conflicting request, this countermeasure QUEUES it and rereads the
// status once the saga resolves, retrying the cancellation if it's still
// valid at that point (a "reread" countermeasure, not just "reject").
import java.util.*;

public class SemanticLockWithReread {
    enum Status { PENDING, CONFIRMED, CANCELLED }
    record Reservation(String orderId, int qty, Status status) {}
    static Map<String, Reservation> reservations = new HashMap<>();
    static Queue<String> pendingCancellationRetries = new LinkedList<>(); // deferred, not rejected outright

    static void reserveStock(String orderId, int qty) {
        reservations.put(orderId, new Reservation(orderId, qty, Status.PENDING));
        System.out.println("inventory: reserved " + qty + " for " + orderId + ", status=PENDING");
    }

    static void tryCancelReservation(String orderId) {
        Reservation r = reservations.get(orderId);
        if (r.status() == Status.PENDING) {
            pendingCancellationRetries.add(orderId); // DEFER, don't reject outright
            System.out.println("cleanup job: " + orderId + " is PENDING -- queued to REREAD after the saga settles");
            return;
        }
        applyCancellation(orderId);
    }

    static void applyCancellation(String orderId) {
        Reservation r = reservations.get(orderId);
        if (r.status() == Status.CONFIRMED) {
            System.out.println("cleanup job: " + orderId + " ended up CONFIRMED -- cancellation no longer valid, skipping");
        } else {
            reservations.remove(orderId);
            System.out.println("cleanup job: " + orderId + " cancelled (was CANCELLED or otherwise eligible)");
        }
    }

    static void onSagaCompleted(String orderId, boolean paymentSucceeded) {
        Status finalStatus = paymentSucceeded ? Status.CONFIRMED : Status.CANCELLED;
        reservations.put(orderId, new Reservation(orderId, reservations.get(orderId).qty(), finalStatus));
        System.out.println("inventory: saga for " + orderId + " settled -> " + finalStatus);

        while (pendingCancellationRetries.remove(orderId)) { // retry any deferred cancellation for this order
            System.out.println("cleanup job: rereading status for " + orderId + " now that the saga settled");
            applyCancellation(orderId);
        }
    }

    public static void main(String[] args) {
        reserveStock("order-1", 5);
        tryCancelReservation("order-1"); // deferred, saga still PENDING

        onSagaCompleted("order-1", false); // saga's payment step FAILS -> reservation should indeed be cancelled

        System.out.println("Final reservations map: " + reservations);
    }
}
```

How to run: `java SemanticLockWithReread.java`

`tryCancelReservation` sees `PENDING` and defers the request into `pendingCancellationRetries` rather than rejecting it forever. When `onSagaCompleted` later runs (here, with `paymentSucceeded=false`, meaning the saga's own compensation should cancel the reservation anyway), it updates the status to `CANCELLED` and then drains `pendingCancellationRetries` for this order, calling `applyCancellation` again — this time the status is no longer `PENDING`, so `applyCancellation` proceeds to actually remove the reservation. The deferred request is thus correctly honored once it is safe to do so, rather than being permanently rejected the way Level 2 handled it.

## 6. Walkthrough

Trace `SemanticLockWithReread.main` in order. **First**, `reserveStock("order-1", 5)` runs, storing a `Reservation` with `status=PENDING`.

**Next**, `tryCancelReservation("order-1")` runs. It reads the current reservation, sees `status() == Status.PENDING`, and takes the deferral branch: `"order-1"` is added to `pendingCancellationRetries`, and a message is printed noting the request is queued rather than rejected or applied.

**Then**, `onSagaCompleted("order-1", false)` runs, simulating the saga's payment step having failed. It computes `finalStatus = Status.CANCELLED` (since `paymentSucceeded` is `false`) and updates the stored reservation to that status. It then enters the `while` loop, which repeatedly checks `pendingCancellationRetries.remove("order-1")` — this returns `true` the first time (removing the queued entry) and calls `applyCancellation("order-1")`.

**Inside this `applyCancellation` call**, the reservation's status is now `CANCELLED`, not `CONFIRMED`, so the `else` branch executes: `reservations.remove("order-1")` runs, and a message confirms the cancellation was applied. The `while` loop then checks `pendingCancellationRetries.remove("order-1")` again, which now returns `false` (nothing left queued for this order), ending the loop.

**Finally**, `main` prints the `reservations` map, which no longer contains an entry for `"order-1"` — the originally deferred cancellation was correctly retried and applied once the saga settled into a state where cancelling was actually the right outcome.

```
reserveStock          -> status=PENDING
tryCancelReservation  -> status is PENDING -> DEFERRED (queued, not rejected)
onSagaCompleted(false)-> status=CANCELLED -> drains queue -> applyCancellation -> reservation REMOVED
```

## 7. Gotchas & takeaways

> A semantic lock is enforced entirely by application code choosing to check it — unlike a database row lock, nothing stops a careless code path from ignoring the status field and acting on the record anyway. Every operation that could conflict with an in-flight saga must be deliberately written to check the semantic lock; there's no engine-level guarantee.

- A semantic lock is just a status field (`PENDING`, `CONFIRMED`, `CANCELLED`) that marks a record as mid-saga, so other code can recognize and handle that state deliberately.
- Common countermeasures: **reject** the conflicting operation outright, **defer and reread** once the saga settles (as in Level 3), or design updates to be **commutative** so ordering doesn't matter.
- Because sagas avoid cross-service database locks by design (see [why 2PC/XA is avoided in microservices](0318-why-2pc-xa-is-avoided-in-microservices.md)), semantic locks are the practical substitute wherever visible intermediate state could mislead another operation.
- Related risks around concurrent access to saga-intermediate data are covered in [saga isolation anomalies](0325-saga-isolation-anomalies-dirty-reads-lost-updates.md).
