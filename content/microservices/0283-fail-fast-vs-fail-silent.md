---
card: microservices
gi: 283
slug: fail-fast-vs-fail-silent
title: "Fail fast vs fail silent"
---

## 1. What it is

Fail fast and fail silent are two opposite philosophies for how a system should react to detecting a problem. Fail fast means surfacing the failure immediately and loudly — throwing an exception, returning an error status, refusing to proceed — as soon as the problem is detected, so it cannot go unnoticed and cannot corrupt later processing. Fail silent means suppressing the failure and continuing as if nothing went wrong, often substituting a default value, an empty result, or simply skipping the failed step, so the failure never becomes visible to the caller or to monitoring.

## 2. Why & when

Fail fast is the right default for most conditions, because it makes bugs and outages immediately visible where they happen, with an accurate stack trace and context, rather than letting corrupted or nonsensical state silently propagate downstream where it becomes far harder to trace back to its root cause. A misconfigured client, a broken invariant, or an unexpected null should almost always fail fast — deferring the failure only makes debugging harder later.

Fail silent has a narrow but real place: it is appropriate when a failure is genuinely non-critical and a sensible default truly exists — which overlaps heavily with [fallback methods](0282-fallback-methods-default-responses.md), but fail-silent specifically means the failure is not surfaced or logged at all, versus a fallback that (done well) still records that the primary path failed. Silently swallowing exceptions with no logging, no metric, and no fallback reasoning is almost never correct — it is a common source of "it's been broken for weeks and nobody noticed" incidents.

Use fail fast as the default posture for anything touching correctness, data integrity, or security. Reserve intentional, *observed* fail-silent behavior (i.e., a logged/metered fallback, not a bare empty catch block) for genuinely optional, cosmetic, or best-effort operations.

## 3. Core concept

Fail fast: detect the problem, stop, and propagate it clearly. Fail silent (done badly): swallow it with no trace. Fail silent (done responsibly, effectively a fallback): swallow it but still record that it happened.

```java
// FAIL FAST -- an invalid state is impossible to miss.
void processOrder(Order order) {
    if (order.total() < 0) throw new IllegalStateException("negative order total: " + order.total());
    // ... proceed only with a KNOWN-VALID order
}

// FAIL SILENT, DONE BADLY -- the bug disappears, so does any signal it happened.
void logAnalyticsEventBad(Event event) {
    try { analyticsClient.send(event); } catch (Exception ignored) { /* nothing */ }
}

// FAIL SILENT, DONE RESPONSIBLY -- non-critical, but still OBSERVABLE.
void logAnalyticsEventGood(Event event) {
    try { analyticsClient.send(event); }
    catch (Exception e) { metrics.increment("analytics.send.failed"); log.warn("analytics send failed", e); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fail fast propagates the error immediately and loudly to the caller; fail silent done badly swallows the error with no trace at all; fail silent done responsibly still swallows the error for the caller but records a metric and log so the failure remains observable">
  <rect x="30" y="20" width="170" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="115" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">FAIL FAST: throw, visible now</text>

  <rect x="30" y="75" width="170" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="115" y="99" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">FAIL SILENT (bad): swallowed, gone</text>

  <rect x="30" y="130" width="170" height="35" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="115" y="152" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">FAIL SILENT (good): swallowed + logged/metered</text>

  <text x="380" y="45" fill="#8b949e" font-size="7.5" font-family="sans-serif">visible immediately -&gt; fast root cause</text>
  <text x="380" y="99" fill="#8b949e" font-size="7.5" font-family="sans-serif">invisible -&gt; discovered weeks later, if ever</text>
  <text x="380" y="150" fill="#8b949e" font-size="7.5" font-family="sans-serif">caller unaffected, but still trackable in dashboards</text>
</svg>

Loud and immediate versus quietly swallowed — and swallowed-but-observed is the only acceptable middle ground.

## 5. Runnable example

Scenario: a batch job that silently swallows per-item errors and appears to succeed while quietly losing data, extended to fail fast on the same errors so the problem is caught immediately in testing, and finally combining both — failing fast on critical items while gracefully (and observably) skipping genuinely optional ones, matching real production behavior.

### Level 1 — Basic

```java
// File: SilentBatchJob.java -- swallows every per-item error with an
// EMPTY catch block. The job reports "success" even though several
// items were silently dropped, with zero trace of what happened.
import java.util.List;

public class SilentBatchJob {
    static void processItem(String item) {
        if (item.equals("bad-item")) throw new RuntimeException("failed to process " + item);
    }

    public static void main(String[] args) {
        List<String> items = List.of("item-1", "item-2", "bad-item", "item-4", "bad-item", "item-6");
        int processed = 0;
        for (String item : items) {
            try {
                processItem(item);
                processed++;
            } catch (Exception ignored) {
                // SILENTLY dropped -- no log, no metric, no trace anywhere.
            }
        }
        System.out.println("Job finished. Processed: " + processed + "/" + items.size()
                + " -- reported as a clean success, 2 items VANISHED with no record.");
    }
}
```

How to run: `java SilentBatchJob.java`

Six items are processed; two throw and are caught by an empty `catch` block. The job finishes and reports "4/6 processed" with no indication anywhere — no log line, no exception, no metric — that two items failed. Anyone monitoring this job sees a clean exit code and has no way to know data was silently lost, short of manually reconciling counts against the source system.

### Level 2 — Intermediate

```java
// File: FailFastBatchJob.java -- the SAME batch job, but now any item
// failure stops the whole job immediately and propagates the error
// loudly, making the problem impossible to miss (at the cost of
// abandoning the remaining, otherwise-processable items).
import java.util.List;

public class FailFastBatchJob {
    static void processItem(String item) {
        if (item.equals("bad-item")) throw new RuntimeException("failed to process " + item);
    }

    public static void main(String[] args) {
        List<String> items = List.of("item-1", "item-2", "bad-item", "item-4", "bad-item", "item-6");
        int processed = 0;
        for (String item : items) {
            processItem(item); // no try/catch -- let it propagate IMMEDIATELY
            processed++;
        }
        System.out.println("Job finished. Processed: " + processed + "/" + items.size());
    }
}
```

How to run: `java FailFastBatchJob.java`

This time there is no error handling at all around `processItem`. The loop reaches `"bad-item"` on the third iteration and the `RuntimeException` propagates straight out of `main`, crashing the program with a visible stack trace and a non-zero exit code. `System.out.println` at the end never even executes. This makes the failure instantly obvious — but at the cost of abandoning `item-4` and `item-6`, which were perfectly processable, purely because they came after the failing item in this batch.

### Level 3 — Advanced

```java
// File: DifferentiatedFailurePolicy.java -- combines both: items marked
// CRITICAL fail the whole job immediately (fail fast), while items
// marked OPTIONAL are skipped on failure but STILL recorded via a metric
// and a per-item error log, so nothing is silently lost even though the
// job as a whole can still succeed.
import java.util.List;
import java.util.ArrayList;

public class DifferentiatedFailurePolicy {
    enum Criticality { CRITICAL, OPTIONAL }
    record Item(String name, Criticality criticality) {}

    static void processItem(Item item) {
        if (item.name().startsWith("bad")) throw new RuntimeException("failed to process " + item.name());
    }

    static class JobMetrics {
        int succeeded = 0;
        final List<String> skippedWithError = new ArrayList<>();
        void recordSkipped(String itemName, Exception e) {
            skippedWithError.add(itemName + " (" + e.getMessage() + ")");
        }
    }

    public static void main(String[] args) {
        List<Item> items = List.of(
                new Item("item-1", Criticality.CRITICAL),
                new Item("bad-optional-item", Criticality.OPTIONAL),
                new Item("item-3", Criticality.CRITICAL),
                new Item("bad-critical-item", Criticality.CRITICAL),
                new Item("item-5", Criticality.CRITICAL)
        );

        JobMetrics metrics = new JobMetrics();
        for (Item item : items) {
            try {
                processItem(item);
                metrics.succeeded++;
            } catch (Exception e) {
                if (item.criticality() == Criticality.CRITICAL) {
                    // FAIL FAST: a critical item failing means the whole job's correctness is in question.
                    System.out.println("ABORTING job: critical item '" + item.name() + "' failed: " + e.getMessage());
                    System.out.println("Progress before abort: succeeded=" + metrics.succeeded
                            + " skipped(optional)=" + metrics.skippedWithError);
                    throw e; // propagate loudly -- do NOT continue past a critical failure
                }
                // FAIL SILENT (responsibly): optional item, skip it, but RECORD it.
                metrics.recordSkipped(item.name(), e);
            }
        }
        System.out.println("Job completed. succeeded=" + metrics.succeeded
                + " skipped(optional, logged)=" + metrics.skippedWithError);
    }
}
```

How to run: `java DifferentiatedFailurePolicy.java`

Five items are processed, three critical and one optional-and-failing, one critical-and-failing. `item-1` and `item-3` (critical, succeed) increment `succeeded`. `bad-optional-item` (optional, fails) is caught, recorded via `metrics.recordSkipped` (an observable record, not silence), and the job continues. `bad-critical-item` (critical, fails) is also caught but immediately re-thrown after printing an abort message and the progress so far — the job stops rather than continuing to `item-5`, because a critical item failing means the overall job's correctness can no longer be trusted.

## 6. Walkthrough

Trace `DifferentiatedFailurePolicy.main` in order. **First**, the `items` list is built with five entries, mixing `CRITICAL` and `OPTIONAL` items, two of which are designed to fail (`bad-optional-item`, `bad-critical-item`).

**Item 1 ("item-1", CRITICAL)**: `processItem` doesn't throw (name doesn't start with "bad"), so the `try` block completes and `metrics.succeeded` becomes 1.

**Item 2 ("bad-optional-item", OPTIONAL)**: `processItem` throws `RuntimeException`. The `catch` block runs, checks `item.criticality() == Criticality.CRITICAL` — false, since this item is `OPTIONAL` — so it falls to `metrics.recordSkipped(...)`, which appends `"bad-optional-item (failed to process bad-optional-item)"` to `skippedWithError`. The loop continues to the next item; nothing propagates out of `main` at this point.

**Item 3 ("item-3", CRITICAL)**: succeeds normally, `metrics.succeeded` becomes 2.

**Item 4 ("bad-critical-item", CRITICAL)**: `processItem` throws again. This time, `item.criticality() == Criticality.CRITICAL` is true, so the code prints an abort message showing the state accumulated so far (`succeeded=2 skipped(optional)=[bad-optional-item (...)]`), then executes `throw e` — re-raising the caught exception. This immediately unwinds out of the `for` loop and out of `main` itself.

**Item 5 ("item-5", CRITICAL)** is never reached — the job aborted before getting to it, which is intentional: once a critical item has failed, continuing to process later items risks working on top of an already-compromised or partially-inconsistent state.

**Final program state**: the process exits with an uncaught exception (non-zero exit code, visible stack trace) — matching fail-fast semantics for the critical failure — but the console output already printed the exact progress made and exactly which optional item was skipped and why, before the abort. This is the key difference from pure fail-silent: even the aborted run leaves a clear, actionable trace of what happened and in what order.

```
item-1 (CRITICAL, ok) -> succeeded=1
bad-optional-item (OPTIONAL, fails) -> recorded, skipped, job CONTINUES
item-3 (CRITICAL, ok) -> succeeded=2
bad-critical-item (CRITICAL, fails) -> ABORT: print progress, re-throw
item-5 (CRITICAL) -> NEVER REACHED
```

## 7. Gotchas & takeaways

> An empty `catch (Exception ignored) {}` block is one of the most common sources of silent, long-lived production bugs — the exception disappears entirely, with no log line, no metric, and no way for anyone to discover the failure short of noticing its downstream symptoms much later.

- Fail fast should be the default for anything affecting correctness, data integrity, or security — surfacing a bug immediately, with full context, is always cheaper to debug than discovering it downstream later.
- True fail-silent (no logging, no metric, no trace) is almost never correct; if a failure is genuinely safe to ignore for the caller, it should still be *recorded* — this is really a responsibly-implemented [fallback](0282-fallback-methods-default-responses.md), not blind silence.
- Distinguish critical from optional work explicitly (as in Level 3) so the failure policy — abort everything vs. skip-and-continue — is a deliberate decision per operation, not an accident of which `try/catch` happened to wrap it.
- When choosing to continue past a failure, always ask whether the remaining work can still be trusted — if a critical step failed, later steps that assumed it succeeded may now be operating on invalid state.
