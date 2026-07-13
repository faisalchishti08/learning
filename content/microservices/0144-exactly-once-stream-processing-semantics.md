---
card: microservices
gi: 144
slug: exactly-once-stream-processing-semantics
title: "Exactly-once stream processing semantics"
---

## 1. What it is

Exactly-once stream processing semantics is a stronger guarantee than plain [at-least-once delivery](0118-at-most-once-at-least-once-exactly-once-delivery.md): not just that a message is never silently lost, but that its *effect* on a stream processing job's output and internal state is applied exactly once, even across consumer crashes and restarts — achieved by making the read (consume input), process (update state), and write (produce output) steps atomic together, rather than treating them as three independent operations that could partially fail.

## 2. Why & when

[Idempotent consumers](0127-idempotent-consumers.md) achieve an *effectively* exactly-once outcome for simple point processing (one input causing one discrete effect, deduplicated by a stable id). Stream processing jobs are harder: they often read from one topic, update internal aggregation state, and write to another topic, all as part of processing a single input event — and a crash between any two of those three steps can leave input consumed but output never produced, or output produced twice, or internal state updated without a corresponding output, in ways a simple per-message idempotency check doesn't fully cover on its own.

True exactly-once stream processing semantics matter specifically for streaming aggregations and transformations where partial failure between read/process/write would corrupt the derived state itself, not just cause a duplicate downstream side effect — financial aggregations, running counts and sums feeding further computation, or any pipeline where a subtly wrong intermediate state silently propagates into everything built on top of it. For simple, stateless pass-through processing, [idempotent consumer](0127-idempotent-consumers.md) techniques alone are often sufficient and considerably simpler.

## 3. Core concept

The read-process-write cycle is wrapped in a single atomic transaction: either the input's consumption, the internal state update, and the output's production all commit together, or none of them do — a crash mid-cycle leaves the system exactly as if that cycle had never started, with nothing partially applied.

```java
// the WRONG way: three independent steps, any of which can fail independently
Event input = consumeFrom(inputTopic);       // step 1
state.update(input);                         // step 2 -- crash here leaves state updated but nothing produced
produceTo(outputTopic, deriveOutput(state));  // step 3

// the RIGHT way: one atomic transaction covering all three
beginTransaction();
Event input = consumeFrom(inputTopic);
state.update(input);
produceTo(outputTopic, deriveOutput(state));
commitTransaction(); // ALL three succeed together, or the whole cycle rolls back
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without a transaction, a crash between updating state and producing output leaves state changed but no corresponding output ever produced. With a transaction wrapping read, process, and write together, a crash at any point rolls back the entire cycle, leaving nothing partially applied">
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Without transaction (broken)</text>
  <rect x="30" y="40" width="80" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="70" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">consume</text>
  <rect x="130" y="40" width="80" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="170" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">update state</text>
  <text x="255" y="60" fill="#8b949e" font-size="14" text-anchor="middle" font-family="sans-serif">X</text>
  <rect x="280" y="40" width="80" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="320" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">produce (never happens)</text>
  <text x="195" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">CRASH here -- state changed, no output ever emitted</text>

  <text x="480" y="115" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">With transaction (correct)</text>
  <rect x="380" y="135" width="240" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="157" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">consume + update + produce</text>
  <text x="500" y="180" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">all-or-nothing, atomic</text>
</svg>

Without atomicity, a crash mid-cycle corrupts state; wrapping the whole cycle in a transaction makes it all-or-nothing.

## 5. Runnable example

Scenario: a streaming running-total processor that starts with a non-atomic read-process-write cycle and demonstrates the corruption a mid-cycle crash produces, then wraps the cycle in a simulated transaction so a crash rolls everything back cleanly, and finally shows the transaction correctly committing across multiple successful cycles while still protecting against a crash on any single one.

### Level 1 — Basic

```java
// File: NonAtomicCycleCorruption.java -- consume, update state, produce as THREE
// separate steps; a crash between them leaves state and output permanently out of sync.
import java.util.*;

public class NonAtomicCycleCorruption {
    static double runningTotal = 0;
    static List<Double> outputTopic = new ArrayList<>();

    public static void main(String[] args) {
        List<Double> inputEvents = List.of(10.0, 20.0, 30.0);

        for (int i = 0; i < inputEvents.size(); i++) {
            double input = inputEvents.get(i);
            runningTotal += input; // step 2: update internal state
            if (i == 1) { // simulate a crash AFTER updating state but BEFORE producing output, on the 2nd event
                System.out.println("*** CRASH after updating state for input=" + input + ", BEFORE producing output ***");
                break;
            }
            outputTopic.add(runningTotal); // step 3: produce output
        }

        System.out.println("Internal state (runningTotal): " + runningTotal);
        System.out.println("Output topic actually produced: " + outputTopic);
        System.out.println("BUG: state reflects 3 inputs conceptually processed, but output only has 1 entry -- they've diverged.");
    }
}
```

**How to run:** `javac NonAtomicCycleCorruption.java && java NonAtomicCycleCorruption` (JDK 17+).

Expected output:
```
*** CRASH after updating state for input=20.0, BEFORE producing output ***
Internal state (runningTotal): 30.0
Output topic actually produced: [10.0]
BUG: state reflects 3 inputs conceptually processed, but output only has 1 entry -- they've diverged.
```

`runningTotal` was updated for the second input, but the crash happened before that update's corresponding output was ever produced — internal state and downstream output are now permanently inconsistent.

### Level 2 — Intermediate

```java
// File: AtomicTransactionRollback.java -- wraps consume+update+produce in a
// simulated transaction; a mid-cycle crash rolls EVERYTHING back, leaving no trace.
import java.util.*;

public class AtomicTransactionRollback {
    static double committedRunningTotal = 0;
    static List<Double> committedOutputTopic = new ArrayList<>();

    // simulated transaction: buffers changes, only applies them ALL TOGETHER on commit
    static class Transaction {
        double pendingTotal;
        List<Double> pendingOutput = new ArrayList<>();
        Transaction() { pendingTotal = committedRunningTotal; }

        void updateState(double input) { pendingTotal += input; }
        void produceOutput(double value) { pendingOutput.add(value); }

        void commit() {
            committedRunningTotal = pendingTotal;
            committedOutputTopic.addAll(pendingOutput);
        }
        // no explicit rollback() needed -- if commit() is never called, pending changes simply vanish
    }

    public static void main(String[] args) {
        List<Double> inputEvents = List.of(10.0, 20.0, 30.0);

        for (int i = 0; i < inputEvents.size(); i++) {
            double input = inputEvents.get(i);
            Transaction tx = new Transaction(); // ONE transaction per input event
            tx.updateState(input);
            if (i == 1) { // same crash point as Level 1 -- but now it's WITHIN an uncommitted transaction
                System.out.println("*** CRASH mid-transaction for input=" + input + " -- tx never committed, changes DISCARDED ***");
                break; // tx.commit() is NEVER called -- its pending changes are simply lost, not partially applied
            }
            tx.produceOutput(tx.pendingTotal);
            tx.commit(); // ALL of this cycle's changes become visible together, or not at all
        }

        System.out.println("Committed state (runningTotal): " + committedRunningTotal);
        System.out.println("Committed output topic: " + committedOutputTopic);
        System.out.println("State and output are CONSISTENT -- the crashed cycle left ZERO trace, instead of a partial one.");
    }
}
```

**How to run:** `javac AtomicTransactionRollback.java && java AtomicTransactionRollback` (JDK 17+).

Expected output:
```
*** CRASH mid-transaction for input=20.0 -- tx never committed, changes DISCARDED ***
Committed state (runningTotal): 10.0
Committed output topic: [10.0]
State and output are CONSISTENT -- the crashed cycle left ZERO trace, instead of a partial one.
```

Unlike Level 1's `30.0` internal state against a `[10.0]` output (an inconsistent pair), here both `committedRunningTotal` and `committedOutputTopic` agree: exactly one event's effects made it through, cleanly, with the crashed second event's partial work fully discarded.

### Level 3 — Advanced

```java
// File: MultiCycleWithOneCrash.java -- runs several successful transactional cycles,
// THEN one that crashes mid-way, THEN resumes -- showing state/output stay consistent throughout.
import java.util.*;

public class MultiCycleWithOneCrash {
    static double committedRunningTotal = 0;
    static List<Double> committedOutputTopic = new ArrayList<>();

    static class Transaction {
        double pendingTotal;
        List<Double> pendingOutput = new ArrayList<>();
        Transaction() { pendingTotal = committedRunningTotal; }
        void updateState(double input) { pendingTotal += input; }
        void produceOutput(double value) { pendingOutput.add(value); }
        void commit() {
            committedRunningTotal = pendingTotal;
            committedOutputTopic.addAll(pendingOutput);
        }
    }

    static void processOneCycle(double input, boolean simulateCrash) {
        Transaction tx = new Transaction();
        tx.updateState(input);
        if (simulateCrash) {
            System.out.println("  input=" + input + ": CRASHED mid-cycle, transaction discarded");
            return; // commit() never called
        }
        tx.produceOutput(tx.pendingTotal);
        tx.commit();
        System.out.println("  input=" + input + ": committed successfully, running total now " + committedRunningTotal);
    }

    public static void main(String[] args) {
        double[] inputs = {5.0, 15.0, 25.0, 8.0, 12.0};
        boolean[] crashOn = {false, false, true, false, false}; // the 3rd cycle crashes

        for (int i = 0; i < inputs.length; i++) {
            processOneCycle(inputs[i], crashOn[i]);
        }

        // expected: 5.0 committed, 15.0 committed (total 20), 25.0 CRASHED (skipped entirely),
        // 8.0 committed (total 28), 12.0 committed (total 40) -- the crashed input is simply absent, not partially applied
        System.out.println("Final committed state: " + committedRunningTotal);
        System.out.println("Final committed output: " + committedOutputTopic);
        System.out.println("Note: input 25.0 left NO trace anywhere -- neither in state nor output -- consistent with atomic all-or-nothing semantics.");
    }
}
```

**How to run:** `javac MultiCycleWithOneCrash.java && java MultiCycleWithOneCrash` (JDK 17+).

Expected output:
```
  input=5.0: committed successfully, running total now 5.0
  input=15.0: committed successfully, running total now 20.0
  input=25.0: CRASHED mid-cycle, transaction discarded
  input=8.0: committed successfully, running total now 28.0
  input=12.0: committed successfully, running total now 40.0
Final committed state: 40.0
Final committed output: [5.0, 20.0, 28.0, 40.0]
```

## 6. Walkthrough

1. **Level 1** — `runningTotal += input` executes and takes effect immediately as a direct mutation, fully independent of whether `outputTopic.add(runningTotal)` (the next line) ever runs; the simulated crash on the second iteration demonstrates that these two statements have no atomic relationship to each other at all.
2. **Level 1, the resulting inconsistency** — `runningTotal` ends at `30.0` (reflecting the crash having already applied the second input's update before breaking), while `outputTopic` contains only `[10.0]` — a downstream system trusting `outputTopic` and a monitoring system trusting `runningTotal` would report two different, both-partially-wrong pictures of the same processing job.
3. **Level 2, buffering pending changes** — `Transaction`'s constructor snapshots the currently-committed total into `pendingTotal`; `updateState` and `produceOutput` both modify only the transaction's own pending fields, never touching `committedRunningTotal` or `committedOutputTopic` directly.
4. **Level 2, commit as the single point of visibility** — only `tx.commit()` copies `pendingTotal` into `committedRunningTotal` and appends `pendingOutput` into `committedOutputTopic`; until that call happens, nothing about the transaction is visible to any other part of the program.
5. **Level 2, the crash's actual effect** — because the simulated crash on `i == 1` triggers a `break` before `tx.commit()` is ever reached, that transaction's `pendingTotal` and `pendingOutput` simply become unreachable, garbage-collected local state — `committedRunningTotal` and `committedOutputTopic` remain exactly as they were after the *first* transaction's successful commit, with no partial trace of the second, crashed one.
6. **Level 3, five cycles, one crash** — `processOneCycle` is called once per input; for `input=25.0` (the third cycle), `simulateCrash` is `true`, so the function returns immediately after `tx.updateState(input)` without ever calling `produceOutput` or `commit`.
7. **Level 3, tracing the committed sequence** — `committedRunningTotal` progresses `5.0 -> 20.0` across the first two successful cycles, is completely untouched by the third (crashed) cycle, then continues `20.0 -> 28.0 -> 40.0` across the fourth and fifth — the value `25.0` never appears anywhere in `committedOutputTopic`, and `committedRunningTotal`'s final value of `40.0` is exactly `5+15+8+12`, correctly excluding the crashed input entirely rather than including it partially.

## 7. Gotchas & takeaways

> **Gotcha:** exactly-once semantics apply to a stream processing job's *own* read-process-write cycle, but if that job's output feeds a system outside the transactional boundary (an external HTTP call, a side effect in a different, non-transactional database), that external effect is not covered by the guarantee — a crash after the transaction commits but before (or during) an external side effect can still duplicate or lose that specific external effect; exactly-once processing is only as end-to-end strong as the weakest, least-transactional link in the full pipeline.

- Exactly-once stream processing semantics guarantee that a crash anywhere in a job's read-process-write cycle leaves that cycle's effects either fully applied or entirely absent, never partially applied.
- This is a stronger, more specific guarantee than plain idempotent-consumer deduplication, because it covers the atomicity of updating internal aggregation state *together with* producing corresponding output, not just deduplicating a single discrete effect.
- The mechanism is transactional: buffering all of a cycle's changes and making them visible only via a single, atomic commit, so an interrupted cycle leaves no partial trace.
- This guarantee matters most for streaming aggregations and transformations, where a partially-applied cycle would corrupt derived state itself, not just cause an isolated duplicate side effect.
- The guarantee only covers what's inside the transactional boundary — external side effects triggered by a stream processing job (calls to other services, non-transactional writes) are not automatically protected by it.
