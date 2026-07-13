---
card: microservices
gi: 339
slug: inbox-pattern-for-idempotent-consumption
title: "Inbox pattern for idempotent consumption"
---

## 1. What it is

The **inbox pattern** is the consuming-side counterpart to the [transactional outbox pattern](0331-transactional-outbox-pattern.md): a consumer records the ID of every message it processes into an **inbox table**, in the *same local transaction* as the business change that message triggers. Before processing a message, the consumer checks whether its ID is already in the inbox; if so, it's a duplicate delivery (from at-least-once messaging, or from a retried [outbox relay](0331-transactional-outbox-pattern.md)) and is skipped, rather than being processed — and its side effect applied — a second time.

## 2. Why & when

Every discussion so far of [idempotency in saga steps](0330-idempotency-in-saga-steps.md) has assumed "the handler checks a set of processed IDs" — the inbox pattern is the durable, transactionally-safe way to actually implement that set, instead of an in-memory `HashSet` that would be lost on a crash and restart (silently allowing a message to be reprocessed) or that isn't atomically tied to the business change it guards.

Use the inbox pattern for any consumer whose message processing has a real side effect (a database write, a call to another system) and where processing the same message twice would cause a problem — which, given at-least-once delivery is the norm, is essentially every consumer of an event or command in a microservices system.

## 3. Core concept

Within one local transaction: check whether the incoming message's ID exists in the inbox table; if it does, skip and return without further action; if it doesn't, perform the business change and insert the message's ID into the inbox — both in the same transaction, so a crash between "processed" and "recorded" is impossible: either both happened, or neither did, exactly mirroring the outbox pattern's guarantee on the publishing side.

```java
@Transactional
void handle(OrderPlacedEvent event) {
    if (inboxRepository.existsById(event.eventId())) return; // duplicate, SKIP
    reserveStock(event);                                       // the real side effect
    inboxRepository.save(new InboxEntry(event.eventId()));      // recorded in the SAME transaction
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A message is delivered twice; the first delivery checks the inbox table, finds no entry, performs the side effect and records the message ID atomically; the second delivery checks the inbox, finds the ID already there, and skips">
  <rect x="20" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Delivery 1: msg-id=42</text>
  <rect x="20" y="100" width="180" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="110" y="122" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Delivery 2: msg-id=42</text>

  <line x1="200" y1="37" x2="290" y2="37" stroke="#3fb950" marker-end="url(#a339)"/>
  <rect x="300" y="10" width="200" height="60" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="400" y="32" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">inbox has no msg-id=42</text>
  <text x="400" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">-&gt; apply effect + record ID</text>

  <line x1="200" y1="117" x2="290" y2="117" stroke="#79c0ff" marker-end="url(#a339b)"/>
  <rect x="300" y="100" width="200" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="400" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">inbox HAS msg-id=42 -&gt; SKIP</text>

  <defs>
    <marker id="a339" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a339b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The side effect and the inbox record are written together atomically, so a redelivered message is reliably recognized and skipped.

## 5. Runnable example

Scenario: a stock-reservation consumer that first double-reserves on redelivery due to an in-memory-only check, then fixed with a durable inbox recorded atomically with the reservation, and finally extended to show why the atomicity specifically matters — surviving a simulated crash between the side effect and the record.

### Level 1 — Basic

```java
// File: InMemoryOnlyCheckIsUnsafe.java -- uses an in-memory Set to guard
// against duplicates; a process restart LOSES that set, so a redelivered
// message after a restart is processed AGAIN.
import java.util.*;

public class InMemoryOnlyCheckIsUnsafe {
    static Map<String, Integer> stockReserved = new HashMap<>();
    static Set<String> processedInMemory = new HashSet<>(); // LOST on restart!

    static void reserveStock(String orderId, int qty, String eventId) {
        if (!processedInMemory.add(eventId)) { System.out.println("SKIPPED duplicate (in-memory check): " + eventId); return; }
        stockReserved.merge(orderId, qty, Integer::sum);
        System.out.println("reserved " + qty + " for " + orderId + " (event " + eventId + ")");
    }

    public static void main(String[] args) {
        reserveStock("order-1", 5, "evt-1");

        System.out.println("--- process RESTARTS here -- processedInMemory is now EMPTY again ---");
        processedInMemory = new HashSet<>(); // simulates the in-memory set being lost on restart

        reserveStock("order-1", 5, "evt-1"); // SAME event, redelivered after restart -- but looks "new" to the empty set!

        System.out.println("Total reserved: " + stockReserved.get("order-1") + " -- should be 5, but DOUBLE-RESERVED after the restart!");
    }
}
```

How to run: `java InMemoryOnlyCheckIsUnsafe.java`

`processedInMemory` correctly prevents a duplicate *within* the same process run, but the simulated restart resets it to empty — the second call for the exact same `eventId="evt-1"` looks brand new to the now-empty set, so it reserves stock a second time. The final total incorrectly shows `10` instead of `5`, purely because the "already processed" memory didn't survive the restart.

### Level 2 — Intermediate

```java
// File: DurableInboxSurvivesRestart.java -- the "processed" record is
// stored in a DURABLE inbox (simulated as a structure that survives the
// restart, unlike the in-memory Set), so a redelivered message after a
// restart is correctly recognized as a duplicate.
import java.util.*;

public class DurableInboxSurvivesRestart {
    static Map<String, Integer> stockReserved = new HashMap<>();
    static Set<String> durableInbox = new HashSet<>(); // simulates a table backed by real, durable storage

    static void reserveStock(String orderId, int qty, String eventId) {
        if (!durableInbox.add(eventId)) { System.out.println("SKIPPED duplicate (durable inbox check): " + eventId); return; }
        stockReserved.merge(orderId, qty, Integer::sum);
        System.out.println("reserved " + qty + " for " + orderId + " (event " + eventId + ")");
    }

    public static void main(String[] args) {
        reserveStock("order-1", 5, "evt-1");

        System.out.println("--- process RESTARTS here -- but durableInbox is BACKED BY DURABLE STORAGE, so it SURVIVES ---");
        // durableInbox is deliberately NOT reset here, unlike processedInMemory in Level 1

        reserveStock("order-1", 5, "evt-1"); // SAME event, redelivered after restart -- correctly recognized this time

        System.out.println("Total reserved: " + stockReserved.get("order-1") + " -- CORRECT, restart didn't cause a double-reservation.");
    }
}
```

How to run: `java DurableInboxSurvivesRestart.java`

The only structural difference from Level 1 is that `durableInbox` is never reset to simulate the restart — standing in for the fact that a real inbox table lives in the database, which genuinely survives a process crash and restart, unlike an in-memory `HashSet`. The redelivered `"evt-1"` is correctly recognized as already processed, and the total stays at the correct `5`.

### Level 3 — Advanced

```java
// File: AtomicInboxAndSideEffect.java -- demonstrates WHY the inbox
// record and the side effect must be written in the SAME transaction: a
// crash BETWEEN performing the reservation and recording the inbox entry
// would otherwise let a retry reserve stock a SECOND time, even with a
// durable inbox, if the two writes aren't atomic together.
import java.util.*;

public class AtomicInboxAndSideEffect {
    static Map<String, Integer> stockReserved = new HashMap<>();
    static Set<String> durableInbox = new HashSet<>();

    // NON-atomic version: two SEPARATE steps -- a crash between them is unsafe.
    static void reserveStockNonAtomic(String orderId, int qty, String eventId, boolean simulateCrashBeforeInboxWrite) {
        if (durableInbox.contains(eventId)) { System.out.println("SKIPPED (non-atomic): " + eventId); return; }
        stockReserved.merge(orderId, qty, Integer::sum); // side effect happens FIRST
        System.out.println("non-atomic: reserved " + qty + " for " + orderId);
        if (simulateCrashBeforeInboxWrite) {
            System.out.println("  ** CRASH ** before the inbox entry was ever written -- inbox still doesn't have " + eventId + "!");
            return; // durableInbox.add(eventId) NEVER RUNS
        }
        durableInbox.add(eventId);
    }

    // ATOMIC version: both writes happen together, or the whole thing is retried from scratch (simulated).
    static void reserveStockAtomic(String orderId, int qty, String eventId) {
        if (durableInbox.contains(eventId)) { System.out.println("SKIPPED (atomic check): " + eventId); return; }
        stockReserved.merge(orderId, qty, Integer::sum);
        durableInbox.add(eventId); // both writes modeled as ONE atomic transaction -- no crash window between them
        System.out.println("atomic: reserved " + qty + " for " + orderId + " and recorded inbox entry TOGETHER");
    }

    public static void main(String[] args) {
        reserveStockNonAtomic("order-1", 5, "evt-1", true); // crashes AFTER reserving, BEFORE recording
        reserveStockNonAtomic("order-1", 5, "evt-1", false); // retry -- inbox STILL doesn't have evt-1, so it reserves AGAIN
        System.out.println("Non-atomic total: " + stockReserved.get("order-1") + " -- WRONG, double-reserved due to the crash window.");

        reserveStockAtomic("order-2", 5, "evt-2");
        reserveStockAtomic("order-2", 5, "evt-2"); // retry of the SAME event -- correctly skipped, since the atomic write already recorded it
        System.out.println("Atomic total: " + stockReserved.get("order-2") + " -- CORRECT, exactly once.");
    }
}
```

How to run: `java AtomicInboxAndSideEffect.java`

`reserveStockNonAtomic`'s first call performs the reservation (`stockReserved` becomes `5`) but is told to simulate a crash *before* `durableInbox.add(eventId)` runs — so the inbox never learns `"evt-1"` was processed. When the same event is retried, `durableInbox.contains("evt-1")` is still `false`, so the reservation happens *again*, bringing the total to `10` — a double-reservation caused entirely by the gap between the side effect and the inbox record. `reserveStockAtomic`, by contrast, performs both writes together with no such gap; its second call for the identical `"evt-2"` correctly finds the inbox entry already present and skips, leaving the total correctly at `5`.

## 6. Walkthrough

Trace `AtomicInboxAndSideEffect.main` in order. **First**, `reserveStockNonAtomic("order-1", 5, "evt-1", true)` runs: `durableInbox.contains("evt-1")` is `false`, so it proceeds; `stockReserved.merge(...)` runs, setting the total to `5`; then, because `simulateCrashBeforeInboxWrite` is `true`, the method prints the crash message and returns *before* reaching `durableInbox.add(eventId)` — the inbox is left without any record of `"evt-1"`.

**Next**, `reserveStockNonAtomic("order-1", 5, "evt-1", false)` runs, representing a retry of the same event after the "crash." `durableInbox.contains("evt-1")` is still `false` (it was never written), so the method proceeds *again*: `stockReserved.merge(...)` adds another `5`, bringing the total to `10`. This time `simulateCrashBeforeInboxWrite` is `false`, so `durableInbox.add("evt-1")` finally runs — too late to prevent the double-reservation that already happened.

**Then**, `reserveStockAtomic("order-2", 5, "evt-2")` runs for the first time: `durableInbox.contains("evt-2")` is `false`, so it reserves (total becomes `5`) and immediately adds `"evt-2"` to `durableInbox` in the same method call, modeling one atomic transaction with no gap for a crash to exploit.

**Finally**, `reserveStockAtomic("order-2", 5, "evt-2")` runs a second time, representing a retry or redelivery of the same event. `durableInbox.contains("evt-2")` is now `true`, so the method skips immediately, leaving the total correctly at `5`.

```
Non-atomic: reserve(evt-1) -> total=5 -> CRASH before inbox write -> retry: inbox still missing evt-1 -> reserve AGAIN -> total=10 (WRONG)
Atomic:     reserve(evt-2) -> total=5, inbox records evt-2 TOGETHER -> retry: inbox HAS evt-2 -> SKIPPED -> total=5 (CORRECT)
```

## 7. Gotchas & takeaways

> Writing the business side effect and the inbox record as two separate statements — even both against durable storage — reopens the exact crash-window vulnerability the inbox pattern exists to close. Both writes must be part of the same local transaction, exactly mirroring the outbox pattern's requirement on the publishing side.

- The inbox pattern durably records which message IDs have already been processed, checked and updated in the same local transaction as the message's actual side effect.
- An in-memory-only "already processed" set is unsafe because it's lost on a crash or restart, silently allowing reprocessing of messages that were, from the consumer's true history, already handled.
- The side effect and the inbox record must be atomic together — writing them as two separate steps reintroduces a crash window where a retry can double-apply the effect.
- This is the consuming-side mirror of the [transactional outbox pattern](0331-transactional-outbox-pattern.md), and together they give an end-to-end at-least-once-delivery-safe pipeline: outbox guarantees the event is eventually published, inbox guarantees it's processed effectively-once.
