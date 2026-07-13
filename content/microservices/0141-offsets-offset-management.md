---
card: microservices
gi: 141
slug: offsets-offset-management
title: "Offsets & offset management"
---

## 1. What it is

An offset is a consumer's own bookmark into a [partition](0140-partitioning-partition-keys.md) of a [log-based broker](0139-log-based-brokers-kafka-vs-queue-brokers.md) — a simple, monotonically increasing number recording "the next position I haven't read yet." Offset management is deciding when and how that bookmark gets saved (committed) so that if a consumer crashes and restarts, it knows where to resume, without either reprocessing everything from the start or skipping messages it never actually finished handling.

## 2. Why & when

Unlike a queue broker, where the broker itself tracks per-message delivery state, a log-based broker leaves position-tracking entirely to the consumer — which means *when* a consumer commits its offset relative to *when* it actually finishes processing a message is a real design decision with real consequences: commit too early (before processing completes) and a crash mid-processing loses that message's work silently on restart; commit too late or too infrequently and a crash forces reprocessing of everything since the last commit, which is only safe if that reprocessing is idempotent.

This decision matters for any consumer of a log-based broker, and the right choice depends on what the consumer can tolerate: at-most-once processing (commit before processing, risk losing work on crash), at-least-once processing (commit after processing, risk reprocessing on crash — the safer, more common default, provided handlers are [idempotent](0127-idempotent-consumers.md)), or manually managed offsets for cases needing tighter control than either default provides.

## 3. Core concept

The offset commit can happen automatically on a timer (simple, but imprecise about exactly which messages were actually processed) or manually, exactly after a consumer confirms it has finished handling a specific batch — manual commit gives control over the precise at-most-once versus at-least-once trade-off at the cost of needing to manage it explicitly.

```java
long offset = 0;
while (true) {
    List<Event> batch = log.readFrom(partition, offset);
    for (Event e : batch) {
        process(e);       // do the work FIRST
        offset++;          // advance the LOCAL position
    }
    commitOffset(partition, offset); // THEN persist the bookmark -- after processing, not before
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A consumer reads and processes events 0 through 4, then commits offset 5; if it crashes after processing but before committing, it will reprocess from the last committed offset on restart -- an at-least-once outcome" >
  <rect x="20" y="60" width="580" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">e0</text>
  <text x="180" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">e1</text>
  <text x="290" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">e2</text>
  <text x="400" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">e3</text>
  <text x="510" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">e4</text>

  <text x="290" y="30" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">processed, but crash BEFORE commit</text>
  <line x1="290" y1="35" x2="290" y2="58" stroke="#8b949e" stroke-dasharray="2,2"/>

  <text x="100" y="140" fill="#8b949e" font-size="8" font-family="sans-serif">last COMMITTED offset: 0</text>
  <line x1="100" y1="120" x2="100" y2="58" stroke="#79c0ff" marker-end="url(#arr23)"/>
  <text x="290" y="140" fill="#8b949e" font-size="8" font-family="sans-serif">on restart: reprocess from HERE (offset 0), NOT from where it crashed</text>

  <defs>
    <marker id="arr23" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Only the last committed offset survives a crash; anything processed but not yet committed will be reprocessed on restart.

## 5. Runnable example

Scenario: an order-processing consumer that starts committing offsets automatically on a fixed schedule (showing the imprecision that creates), switches to manual commit-after-processing to make the at-least-once guarantee deliberate and precise, and finally simulates a crash mid-batch to show exactly what gets reprocessed on restart and why that is the correct, expected behavior for a manually-committed, idempotent consumer.

### Level 1 — Basic

```java
// File: AutoCommitImprecision.java -- auto-commit on a timer, DECOUPLED from actual
// processing progress: it can commit an offset for work not yet even attempted.
import java.util.*;

public class AutoCommitImprecision {
    public static void main(String[] args) throws InterruptedException {
        List<String> events = List.of("order:1", "order:2", "order:3", "order:4", "order:5");
        long offset = 0;
        long lastAutoCommitTime = System.currentTimeMillis();
        long autoCommitIntervalMs = 50;
        long committedOffset = 0;

        for (String event : events) {
            System.out.println("Processing " + event + " at offset " + offset);
            Thread.sleep(20); // simulated processing time
            offset++;

            // auto-commit fires on a TIMER, independent of which specific event just finished
            if (System.currentTimeMillis() - lastAutoCommitTime >= autoCommitIntervalMs) {
                committedOffset = offset;
                lastAutoCommitTime = System.currentTimeMillis();
                System.out.println("  [auto-commit fired] committedOffset now " + committedOffset);
            }
        }
        System.out.println("Final committedOffset: " + committedOffset + " vs. actual processed offset: " + offset + " (may LAG behind what was truly processed)");
    }
}
```

**How to run:** `javac AutoCommitImprecision.java && java AutoCommitImprecision` (JDK 17+).

The commit happens whenever the timer fires, not tied to any specific event boundary — `committedOffset` can meaningfully lag behind `offset`, meaning a crash right after the loop ends but before one final auto-commit would silently lose track of the last few processed events' progress.

### Level 2 — Intermediate

```java
// File: ManualCommitAfterProcessing.java -- commit explicitly, immediately after
// each event finishes -- a precise, deliberate at-least-once guarantee.
import java.util.*;

public class ManualCommitAfterProcessing {
    public static void main(String[] args) {
        List<String> events = List.of("order:1", "order:2", "order:3", "order:4", "order:5");
        long offset = 0;
        long committedOffset = 0;

        for (String event : events) {
            System.out.println("Processing " + event + " at offset " + offset);
            processOrder(event); // do the work FIRST
            offset++;
            committedOffset = offset; // THEN commit, immediately, tied exactly to this event's completion
            System.out.println("  committed offset " + committedOffset + " (exactly matches work done)");
        }
        System.out.println("Final committedOffset: " + committedOffset + " -- ALWAYS exactly matches processed offset, never lags.");
    }

    static void processOrder(String event) { /* actual business logic would go here */ }
}
```

**How to run:** `javac ManualCommitAfterProcessing.java && java ManualCommitAfterProcessing` (JDK 17+).

Expected output shows `committedOffset` advancing in lockstep with every single processed event, with no possibility of the gap Level 1 could produce — each commit is tied precisely to the completion of the specific event that triggered it.

### Level 3 — Advanced

```java
// File: CrashRecoverySimulation.java -- simulates a crash mid-batch and shows EXACTLY
// what gets reprocessed on restart, and why idempotent processing makes that safe.
import java.util.*;

public class CrashRecoverySimulation {
    static Set<String> processedOrderIds = new HashSet<>(); // idempotency guard, see idempotent consumers

    public static void main(String[] args) {
        List<String> events = List.of("order:1", "order:2", "order:3", "order:4", "order:5");

        // === "run 1": crashes partway through, AFTER processing order:3 but BEFORE committing offset 3 ===
        long offset = 0;
        long committedOffset = 0; // persisted externally in a real system (e.g. Kafka's __consumer_offsets)
        for (int i = 0; i < events.size(); i++) {
            String event = events.get(i);
            processIdempotently(event);
            offset++;
            if (i == 2) { // crash simulated RIGHT after processing order:3, before this iteration's commit
                System.out.println("*** CRASH after processing " + event + ", BEFORE committing offset " + offset + " ***");
                break;
            }
            committedOffset = offset;
        }
        System.out.println("Run 1 ended. Last COMMITTED offset (persisted, survives crash): " + committedOffset);
        System.out.println("But 'order:3' WAS processed in-memory -- that work's completion was never durably recorded.");

        // === "run 2": restart, resume from the last COMMITTED offset, not from where it crashed ===
        System.out.println("\n--- Consumer restarts ---");
        offset = committedOffset; // resume from offset 2 (order:1, order:2 were committed; order:3 was NOT)
        for (long i = offset; i < events.size(); i++) {
            String event = events.get((int) i);
            processIdempotently(event); // order:3 gets processed AGAIN -- this is expected, at-least-once behavior
            committedOffset = i + 1;
        }
        System.out.println("Run 2 finished. Final committedOffset: " + committedOffset);
        System.out.println("processedOrderIds ended up correct regardless, because processIdempotently guards against the reprocessed 'order:3'.");
    }

    static void processIdempotently(String orderId) {
        if (!processedOrderIds.add(orderId)) { // Set.add returns false if already present
            System.out.println("  [idempotent guard] " + orderId + " already processed -- no-op on reprocess");
            return;
        }
        System.out.println("  processed: " + orderId);
    }
}
```

**How to run:** `javac CrashRecoverySimulation.java && java CrashRecoverySimulation` (JDK 17+).

Expected output:
```
  processed: order:1
  processed: order:2
  processed: order:3
*** CRASH after processing order:3, BEFORE committing offset 3 ***
Run 1 ended. Last COMMITTED offset (persisted, survives crash): 2
But 'order:3' WAS processed in-memory -- that work's completion was never durably recorded.

--- Consumer restarts ---
  [idempotent guard] order:3 already processed -- no-op on reprocess
  processed: order:4
  processed: order:5
Run 2 finished. Final committedOffset: 5
processedOrderIds ended up correct regardless, because processIdempotently guards against the reprocessed 'order:3'.
```

## 6. Walkthrough

1. **Level 1** — `committedOffset` is only updated when `System.currentTimeMillis() - lastAutoCommitTime >= autoCommitIntervalMs` evaluates true, a condition entirely about elapsed wall-clock time, with no relationship to which specific event index just finished processing; the final printed comparison highlights that `committedOffset` and `offset` can genuinely diverge.
2. **Level 2, tying commit to completion** — `committedOffset = offset` executes immediately after `processOrder(event)` returns and `offset` is incremented, on every single loop iteration, so there is no window where processing has outpaced what's committed.
3. **Level 2, the guarantee this produces** — because every commit is precisely tied to the event that just completed, a crash at any point would leave `committedOffset` exactly equal to the count of events genuinely finished — the imprecision Level 1 could exhibit is structurally impossible here.
4. **Level 3, simulating the crash point** — the `if (i == 2)` check deliberately breaks out of the loop *after* `processIdempotently(event)` and `offset++` have run for `"order:3"`, but *before* `committedOffset = offset` executes for that same iteration — modeling a crash landing in the narrow window between finishing work and persisting the bookmark for it.
5. **Level 3, what survives the crash** — `committedOffset` is left at `2` (reflecting only `order:1` and `order:2`), even though `order:3` was genuinely processed and added to `processedOrderIds` during "run 1" — this in-memory fact about `order:3` is lost the instant the simulated crash happens, since only `committedOffset` is treated as durably persisted.
6. **Level 3, restarting from the last commit** — "run 2" sets `offset = committedOffset` (which is `2`), meaning it deliberately starts by reprocessing `"order:3"` — the event that was actually finished in run 1 but never had that fact durably recorded — exactly the expected at-least-once behavior of manual, post-processing commits.
7. **Level 3, why this is safe** — `processIdempotently` checks `processedOrderIds.add(orderId)` before doing any real work, and since `order:3` is already in that set from run 1's execution (both runs share the same `processedOrderIds` static field in this simulation, standing in for state that would live in a real, durable data store), the reprocessing attempt in run 2 is correctly recognized and skipped as a no-op — the offset-management strategy (commit after processing, accept possible reprocessing) is only safe *because* it's paired with [idempotent consumer](0127-idempotent-consumers.md) logic; without that pairing, `order:3` would have been double-processed.

## 7. Gotchas & takeaways

> **Gotcha:** committing an offset *before* processing completes (the opposite ordering from what Level 2 and 3 demonstrate) trades at-least-once for at-most-once — a crash after that early commit but before processing finishes means the message is now considered "done" by the broker's bookkeeping even though it never actually was, silently losing that work; the ordering of "process, then commit" versus "commit, then process" is the entire difference between these two guarantees.

- An offset is the consumer's own bookmark into a partition; unlike a queue broker's per-message tracking, a log-based broker leaves this entirely up to the consumer to manage.
- Auto-commit on a timer is simple but imprecise, since the commit is decoupled from exactly which event finished processing, creating windows where committed and actually-processed progress diverge.
- Manual commit, executed immediately after processing completes, ties the bookmark precisely to real progress and produces a clean, understandable at-least-once guarantee.
- A crash between finishing work and committing its offset causes that work to be reprocessed on restart — expected, correct at-least-once behavior, not a bug.
- This reprocessing is only safe when paired with [idempotent consumer](0127-idempotent-consumers.md) logic; offset management alone does not prevent duplicate processing, it only determines when duplicates can occur.
