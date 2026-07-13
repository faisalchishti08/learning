---
card: microservices
gi: 343
slug: spring-transactional-event-listeners-transactionaleventliste
title: "Spring transactional event listeners (@TransactionalEventListener)"
---

## 1. What it is

`@TransactionalEventListener` is a Spring annotation for event listener methods that ties the listener's execution to the outcome of the transaction that published the event — most commonly configured with `phase = TransactionPhase.AFTER_COMMIT`, meaning the listener only runs if and when the surrounding transaction actually commits successfully. This solves a subtle but important bug that a plain `@EventListener` doesn't handle: reacting to an event whose triggering transaction later rolls back.

## 2. Why & when

If a service publishes a domain event from inside a `@Transactional` method using a plain `@EventListener`, Spring by default invokes that listener *synchronously*, immediately, before the transaction has actually committed. If the transaction subsequently rolls back (a later step in the same method throws), the listener has already run — sending an email, calling another service, publishing to a message broker — for a change that ultimately never took effect. `@TransactionalEventListener` with `AFTER_COMMIT` exists precisely to close this gap: the listener is deferred until Spring confirms the transaction committed, guaranteeing the event's side effects only happen for changes that are actually durable.

Use `@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)` for any listener reacting to a domain event published from within a transactional method, whenever that listener has a real side effect (especially publishing further events, calling other services, or sending notifications) that should only happen if the underlying change genuinely persisted. Other phases exist (`BEFORE_COMMIT`, `AFTER_ROLLBACK`, `AFTER_COMPLETION`) for less common needs, but `AFTER_COMMIT` is the one that matters most often in practice.

## 3. Core concept

Spring registers `@TransactionalEventListener` methods to be invoked by the transaction synchronization mechanism at the specified phase, rather than immediately when the event is published. If there is no active transaction when the event is published, the listener is skipped entirely by default (a common surprise), so this annotation is specifically for events published from within a genuine `@Transactional` context.

```java
@Transactional
public void placeOrder(Order order) {
    orderRepository.save(order);
    applicationEventPublisher.publishEvent(new OrderPlacedEvent(order.getId())); // published NOW
} // listener still WON'T run until this transaction actually commits

@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void onOrderPlaced(OrderPlacedEvent event) { /* runs ONLY after commit */ }
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inside a transaction, an event is published and a save happens; if the transaction later rolls back the listener never runs; if it commits, the listener runs only then, after commit">
  <rect x="30" y="20" width="580" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">@Transactional placeOrder(): save() + publishEvent()</text>
  <text x="320" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">listener is QUEUED, not run yet</text>

  <line x1="200" y1="80" x2="120" y2="120" stroke="#f85149" marker-end="url(#a343)"/>
  <rect x="20" y="120" width="200" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="120" y="142" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ROLLBACK -&gt; listener NEVER runs</text>

  <line x1="440" y1="80" x2="520" y2="120" stroke="#3fb950" marker-end="url(#a343b)"/>
  <rect x="420" y="120" width="200" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="520" y="142" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">COMMIT -&gt; listener runs NOW</text>

  <defs>
    <marker id="a343" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="a343b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The listener's execution is deferred until the surrounding transaction's outcome is known — it never runs for a transaction that rolls back.

## 5. Runnable example

Scenario: an order-placement flow that first uses a plain, immediate listener that incorrectly fires even when the transaction later rolls back, then fixed with a simulated `@TransactionalEventListener`-style deferred listener that only fires after commit, and finally extended to show multiple listeners deferred together, all correctly skipped on rollback.

### Level 1 — Basic

```java
// File: PlainListenerFiresTooEarly.java -- a plain, IMMEDIATE listener
// runs the instant the event is published, even though the transaction
// LATER rolls back -- a real bug: the listener acted on a change that
// never actually took effect.
import java.util.*;

public class PlainListenerFiresTooEarly {
    static Map<String, String> ordersTable = new HashMap<>();
    static List<Runnable> immediateListeners = new ArrayList<>();

    static void publishEventImmediately(String orderId) {
        System.out.println("event published -- listener runs IMMEDIATELY:");
        immediateListeners.forEach(Runnable::run);
    }

    static void placeOrder(String orderId, boolean simulateFailureAfterPublish) {
        ordersTable.put(orderId, "PLACED"); // not yet "committed" in this simulation
        publishEventImmediately(orderId);    // listener runs RIGHT NOW, before we know the outcome
        if (simulateFailureAfterPublish) {
            ordersTable.remove(orderId); // simulates a ROLLBACK -- the "transaction" failed AFTER the event fired
            System.out.println("transaction ROLLED BACK -- but the listener ALREADY ran for a change that never stuck!");
        }
    }

    public static void main(String[] args) {
        immediateListeners.add(() -> System.out.println("  sending confirmation email... (ALREADY SENT, even though order will be rolled back)"));
        placeOrder("order-1", true);
        System.out.println("Final: order-1 in table? " + ordersTable.containsKey("order-1") + " -- email sent anyway. BUG.");
    }
}
```

How to run: `java PlainListenerFiresTooEarly.java`

`publishEventImmediately` runs every registered listener synchronously, the instant it's called — before `placeOrder` even knows whether the surrounding "transaction" will succeed. The listener sends a confirmation email, and only afterward does the code simulate a rollback by removing the order — the email was already sent for an order that, in the end, was never actually placed.

### Level 2 — Intermediate

```java
// File: DeferredAfterCommitListener.java -- listeners are QUEUED during
// the transaction and only actually invoked if the transaction commits;
// a rollback discards the queue entirely, so the listener NEVER runs.
import java.util.*;

public class DeferredAfterCommitListener {
    static Map<String, String> ordersTable = new HashMap<>();
    static List<Runnable> pendingAfterCommitListeners = new ArrayList<>(); // queued, NOT run yet

    static void publishEventDeferred(Runnable listener) {
        pendingAfterCommitListeners.add(listener); // just QUEUE it -- do NOT run it now
        System.out.println("event published -- listener QUEUED for after-commit, not run yet");
    }

    static void runTransactionally(Runnable body) {
        pendingAfterCommitListeners.clear(); // fresh transaction, fresh queue
        boolean committed = false;
        try {
            body.run();
            committed = true; // reached the end without an exception -- "commit"
        } finally {
            if (committed) {
                System.out.println("transaction COMMITTED -- now running " + pendingAfterCommitListeners.size() + " queued listener(s)");
                pendingAfterCommitListeners.forEach(Runnable::run);
            } else {
                System.out.println("transaction ROLLED BACK -- discarding " + pendingAfterCommitListeners.size() + " queued listener(s), NONE will run");
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("--- Scenario: transaction FAILS ---");
        try {
            runTransactionally(() -> {
                ordersTable.put("order-1", "PLACED");
                publishEventDeferred(() -> System.out.println("  sending confirmation email for order-1"));
                throw new RuntimeException("payment failed");
            });
        } catch (RuntimeException e) { System.out.println("caught: " + e.getMessage()); }

        System.out.println("--- Scenario: transaction SUCCEEDS ---");
        runTransactionally(() -> {
            ordersTable.put("order-2", "PLACED");
            publishEventDeferred(() -> System.out.println("  sending confirmation email for order-2"));
        });
    }
}
```

How to run: `java DeferredAfterCommitListener.java`

In the failing scenario, `publishEventDeferred` only queues the email-sending listener; when the lambda then throws, `committed` stays `false`, so the `finally` block's `else` branch discards the queue — the email listener never runs. In the succeeding scenario, the lambda completes normally, `committed` becomes `true`, and the `finally` block's `if` branch actually invokes every queued listener — the email is sent, but only because (and only after) the transaction is known to have committed.

### Level 3 — Advanced

```java
// File: MultipleListenersDeferredTogether.java -- several INDEPENDENT
// listeners (email, analytics, audit log) all subscribe to the same
// event; ALL of them are correctly deferred and either ALL run together
// after commit or NONE run at all after a rollback.
import java.util.*;

public class MultipleListenersDeferredTogether {
    static Map<String, String> ordersTable = new HashMap<>();
    static List<Runnable> pendingAfterCommitListeners = new ArrayList<>();

    static void publishOrderPlacedEvent(String orderId) {
        // Three INDEPENDENT listeners, all subscribing to the same conceptual event -- each is deferred, not run now.
        pendingAfterCommitListeners.add(() -> System.out.println("  [email] confirmation sent for " + orderId));
        pendingAfterCommitListeners.add(() -> System.out.println("  [analytics] order counted for " + orderId));
        pendingAfterCommitListeners.add(() -> System.out.println("  [audit] logged placement of " + orderId));
        System.out.println("event published for " + orderId + " -- 3 listeners queued, none run yet");
    }

    static void runTransactionally(Runnable body) {
        pendingAfterCommitListeners.clear();
        boolean committed = false;
        try {
            body.run();
            committed = true;
        } finally {
            if (committed) {
                System.out.println("COMMIT -- running all " + pendingAfterCommitListeners.size() + " queued listeners together:");
                pendingAfterCommitListeners.forEach(Runnable::run);
            } else {
                System.out.println("ROLLBACK -- discarding all " + pendingAfterCommitListeners.size() + " queued listeners, NONE run");
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("--- order-1: fails validation AFTER the event was published ---");
        try {
            runTransactionally(() -> {
                ordersTable.put("order-1", "PLACED");
                publishOrderPlacedEvent("order-1");
                throw new RuntimeException("inventory check failed");
            });
        } catch (RuntimeException e) { System.out.println("caught: " + e.getMessage()); }

        System.out.println("--- order-2: succeeds ---");
        runTransactionally(() -> {
            ordersTable.put("order-2", "PLACED");
            publishOrderPlacedEvent("order-2");
        });
    }
}
```

How to run: `java MultipleListenersDeferredTogether.java`

For `order-1`, all three listeners (email, analytics, audit) are queued when `publishOrderPlacedEvent` runs, but the subsequent `RuntimeException` means `committed` stays `false` — all three are discarded together, and none of them run; no email is sent, no analytics count is recorded, no audit entry is logged, correctly matching the fact that the order was never really placed. For `order-2`, the same three listeners are queued and, because the transaction completes normally this time, all three run together after commit — demonstrating that `@TransactionalEventListener`'s deferral applies uniformly to every listener subscribing to a transactional event, not just one.

## 6. Walkthrough

Trace `MultipleListenersDeferredTogether.main` in order. **First**, the `order-1` scenario calls `runTransactionally` with a lambda that puts `"order-1"` into `ordersTable`, calls `publishOrderPlacedEvent("order-1")` (which appends three listener lambdas to `pendingAfterCommitListeners` and prints that they're queued), and then throws a `RuntimeException`.

**Inside `runTransactionally`**, the `try` block's `body.run()` call propagates that exception before reaching `committed = true` — so `committed` remains `false`. The `finally` block then runs regardless, and since `committed` is `false`, the `else` branch executes: it prints that the transaction rolled back and explicitly discards the queue without invoking any of the three listeners.

**The exception then propagates out of `runTransactionally`**, is caught by `main`'s `try/catch`, and printed.

**Next**, the `order-2` scenario calls `runTransactionally` again, with `pendingAfterCommitListeners.clear()` first resetting the queue for this new transaction. Its lambda puts `"order-2"` into `ordersTable`, calls `publishOrderPlacedEvent("order-2")` (queuing three fresh listeners), and completes normally — no exception this time.

**Back in `runTransactionally`**, `committed` is set to `true` after `body.run()` returns successfully. The `finally` block's `if` branch then runs, printing a commit message and invoking all three queued listeners in sequence — the email, analytics, and audit listeners all execute, since the transaction is now known to have genuinely committed.

```
order-1: publish -> 3 listeners QUEUED -> body throws -> committed=false -> ROLLBACK -> discard ALL 3, NONE run
order-2: publish -> 3 listeners QUEUED -> body completes -> committed=true -> COMMIT -> run ALL 3 together
```

## 7. Gotchas & takeaways

> `@TransactionalEventListener` methods are, by default, silently skipped entirely if there is no active transaction when the event is published — a common surprise when testing a listener in isolation, or when the publishing code isn't actually running inside a `@Transactional` method. Confirm the publisher genuinely runs within a transaction before relying on this annotation's after-commit guarantee.

- `@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)` defers a listener's execution until the surrounding transaction is confirmed to have committed, unlike a plain `@EventListener`, which runs immediately and synchronously.
- This prevents listeners with real side effects (emails, further events, external calls) from firing for changes that ultimately roll back.
- Every listener subscribing to the same transactional event is deferred the same way — a rollback discards all of them together, a commit runs all of them together.
- This pattern pairs naturally with the [transactional outbox pattern](0331-transactional-outbox-pattern.md) and with [Spring Modulith's event publication registry](0344-spring-modulith-event-publication-registry-outbox-style.md), which builds a similar guarantee directly into event publication itself.
